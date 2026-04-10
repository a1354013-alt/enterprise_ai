from __future__ import annotations

import hashlib
import hmac
import logging
import os
import secrets
import sqlite3
from datetime import datetime, timezone
from typing import Any

try:
    import chromadb
    from chromadb.utils import embedding_functions
except ImportError:  # pragma: no cover - optional runtime dependency
    chromadb = None
    embedding_functions = None


logger = logging.getLogger("enterprise_ai")

_EMBEDDING_FUNCTION = None
_COLLECTION = None
_PASSWORD_ITERATIONS = 120000


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    derived = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), _PASSWORD_ITERATIONS)
    return f'{salt}${derived.hex()}'


def verify_password_hash(password: str, stored_hash: str) -> bool:
    try:
        salt, expected = stored_hash.split('$', 1)
    except ValueError:
        return False
    computed = hash_password(password, salt).split('$', 1)[1]
    return hmac.compare_digest(computed, expected)


def get_embedding_function():
    global _EMBEDDING_FUNCTION
    if _EMBEDDING_FUNCTION is not None:
        return _EMBEDDING_FUNCTION
    if embedding_functions is None:
        raise RuntimeError('chromadb is not installed.')

    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    if openai_key:
        try:
            from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

            _EMBEDDING_FUNCTION = OpenAIEmbeddingFunction(
                api_key=openai_key,
                model_name="text-embedding-3-small",
            )
            logger.info("Using OpenAI embeddings.")
            return _EMBEDDING_FUNCTION
        except Exception as exc:
            logger.warning("OpenAI embeddings unavailable, falling back to local model: %s", exc)

    _EMBEDDING_FUNCTION = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    logger.info("Using sentence-transformers embeddings.")
    return _EMBEDDING_FUNCTION


class DocumentDatabase:
    def __init__(self, db_path: str = "documents.db"):
        self.db_path = db_path
        self._memory_conn: sqlite3.Connection | None = None
        self.init_db()

    def _connect(self) -> sqlite3.Connection:
        if self.db_path == ':memory:':
            if self._memory_conn is None:
                self._memory_conn = sqlite3.connect(':memory:', check_same_thread=False)
                self._memory_conn.row_factory = sqlite3.Row
            return self._memory_conn

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                display_name TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'employee',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                doc_id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                saved_filename TEXT NOT NULL,
                allowed_roles TEXT NOT NULL,
                uploaded_by TEXT,
                uploaded_at TEXT NOT NULL,
                file_size INTEGER NOT NULL DEFAULT 0,
                approved INTEGER NOT NULL DEFAULT 0,
                is_active INTEGER NOT NULL DEFAULT 1,
                updated_at TEXT NOT NULL
            )
            """
        )
        self._migrate_documents_table(cursor)
        self._seed_admin_user(cursor)
        conn.commit()
        if self.db_path != ':memory:':
            conn.close()

    def _migrate_documents_table(self, cursor: sqlite3.Cursor) -> None:
        cursor.execute("PRAGMA table_info(documents)")
        columns = {row[1] for row in cursor.fetchall()}
        migrations = {
            "uploaded_by": "ALTER TABLE documents ADD COLUMN uploaded_by TEXT",
            "approved": "ALTER TABLE documents ADD COLUMN approved INTEGER NOT NULL DEFAULT 0",
            "is_active": "ALTER TABLE documents ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1",
            "updated_at": "ALTER TABLE documents ADD COLUMN updated_at TEXT NOT NULL DEFAULT ''",
            "file_size": "ALTER TABLE documents ADD COLUMN file_size INTEGER NOT NULL DEFAULT 0",
        }
        for column, sql in migrations.items():
            if column not in columns:
                cursor.execute(sql)
        cursor.execute("UPDATE documents SET updated_at = uploaded_at WHERE updated_at = ''")

    def _seed_admin_user(self, cursor: sqlite3.Cursor) -> None:
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] > 0:
            return

        default_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin12345")
        now = utc_now_iso()
        password_hash = hash_password(default_password)
        cursor.execute(
            """
            INSERT INTO users (user_id, password_hash, display_name, role, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("admin", password_hash, "Administrator", "admin", 1, now, now),
        )
        logger.warning("Seeded default admin account 'admin'. Change DEFAULT_ADMIN_PASSWORD for production.")

    def get_user(self, user_id: str) -> dict[str, Any] | None:
        conn = self._connect()
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if self.db_path != ':memory:':
            conn.close()
        return dict(row) if row else None

    def verify_password(self, user_id: str, password: str) -> bool:
        user = self.get_user(user_id)
        if not user:
            return False
        return verify_password_hash(password, user["password_hash"])

    def list_users(self) -> list[dict[str, Any]]:
        conn = self._connect()
        rows = conn.execute(
            """
            SELECT user_id, display_name, role, is_active, created_at, updated_at
            FROM users
            ORDER BY created_at ASC
            """
        ).fetchall()
        if self.db_path != ':memory:':
            conn.close()
        return [dict(row) for row in rows]

    def add_user(self, user_id: str, password: str, display_name: str, role: str, is_active: int = 1) -> bool:
        now = utc_now_iso()
        password_hash = hash_password(password)
        try:
            conn = self._connect()
            conn.execute(
                """
                INSERT INTO users (user_id, password_hash, display_name, role, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, password_hash, display_name, role, is_active, now, now),
            )
            conn.commit()
            if self.db_path != ':memory:':
                conn.close()
            return True
        except sqlite3.IntegrityError:
            return False

    def update_user(self, user_id: str, **updates: Any) -> bool:
        columns: list[str] = []
        params: list[Any] = []

        if "display_name" in updates:
            columns.append("display_name = ?")
            params.append(updates["display_name"])
        if "role" in updates:
            columns.append("role = ?")
            params.append(updates["role"])
        if "is_active" in updates:
            columns.append("is_active = ?")
            params.append(updates["is_active"])
        if "password" in updates:
            columns.append("password_hash = ?")
            params.append(hash_password(updates["password"]))
        if not columns:
            return False

        columns.append("updated_at = ?")
        params.append(utc_now_iso())
        params.append(user_id)

        conn = self._connect()
        cursor = conn.execute(
            f"UPDATE users SET {', '.join(columns)} WHERE user_id = ?",
            params,
        )
        conn.commit()
        if self.db_path != ':memory:':
            conn.close()
        return cursor.rowcount > 0

    def add_document(
        self,
        doc_id: str,
        filename: str,
        saved_filename: str,
        allowed_roles: list[str],
        file_size: int,
        uploaded_by: str | None,
    ) -> bool:
        now = utc_now_iso()
        try:
            conn = self._connect()
            conn.execute(
                """
                INSERT INTO documents
                (doc_id, filename, saved_filename, allowed_roles, uploaded_by, uploaded_at, file_size, approved, is_active, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0, 1, ?)
                """,
                (doc_id, filename, saved_filename, ",".join(allowed_roles), uploaded_by, now, file_size, now),
            )
            conn.commit()
            if self.db_path != ':memory:':
                conn.close()
            return True
        except sqlite3.IntegrityError:
            return False

    def _normalize_document_row(self, row: sqlite3.Row) -> dict[str, Any]:
        document = dict(row)
        document["allowed_roles"] = [role for role in document["allowed_roles"].split(",") if role]
        document["approved"] = int(document["approved"])
        document["is_active"] = int(document["is_active"])
        return document

    def get_document(self, doc_id: str) -> dict[str, Any] | None:
        conn = self._connect()
        row = conn.execute("SELECT * FROM documents WHERE doc_id = ?", (doc_id,)).fetchone()
        if self.db_path != ':memory:':
            conn.close()
        return self._normalize_document_row(row) if row else None

    def list_documents(self) -> list[dict[str, Any]]:
        conn = self._connect()
        rows = conn.execute("SELECT * FROM documents ORDER BY uploaded_at DESC").fetchall()
        if self.db_path != ':memory:':
            conn.close()
        return [self._normalize_document_row(row) for row in rows]

    def update_document(self, doc_id: str, **updates: Any) -> bool:
        columns: list[str] = []
        params: list[Any] = []
        if "allowed_roles" in updates:
            columns.append("allowed_roles = ?")
            params.append(",".join(updates["allowed_roles"]))
        if "approved" in updates:
            columns.append("approved = ?")
            params.append(int(updates["approved"]))
        if "is_active" in updates:
            columns.append("is_active = ?")
            params.append(int(updates["is_active"]))
        if not columns:
            return False

        columns.append("updated_at = ?")
        params.append(utc_now_iso())
        params.append(doc_id)

        conn = self._connect()
        cursor = conn.execute(
            f"UPDATE documents SET {', '.join(columns)} WHERE doc_id = ?",
            params,
        )
        conn.commit()
        if self.db_path != ':memory:':
            conn.close()
        return cursor.rowcount > 0

    def delete_document(self, doc_id: str) -> bool:
        conn = self._connect()
        cursor = conn.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
        conn.commit()
        if self.db_path != ':memory:':
            conn.close()
        return cursor.rowcount > 0


def get_collection():
    global _COLLECTION
    if _COLLECTION is not None:
        return _COLLECTION
    if chromadb is None:
        raise RuntimeError('chromadb is not installed.')

    client = chromadb.PersistentClient(path=os.getenv("CHROMA_DB_PATH", "./chroma_db"))
    _COLLECTION = client.get_or_create_collection(
        name="documents",
        embedding_function=get_embedding_function(),
        metadata={"hnsw:space": "cosine"},
    )
    return _COLLECTION


def add_to_vector_db(
    doc_id: str,
    chunks: list[str],
    metadata_list: list[dict[str, Any]],
    allowed_roles: list[str] | None = None,
) -> bool:
    if chromadb is None:
        logger.warning('chromadb not installed; skipping vector indexing for %s.', doc_id)
        return True
    try:
        collection = get_collection()
        ids = [f"{doc_id}_{index}" for index in range(len(chunks))]
        active_roles = allowed_roles or []

        for metadata in metadata_list:
            metadata["role_employee"] = "employee" in active_roles
            metadata["role_manager"] = "manager" in active_roles
            metadata["role_hr"] = "hr" in active_roles
            metadata["role_admin"] = "admin" in active_roles

        collection.add(ids=ids, documents=chunks, metadatas=metadata_list)
        return True
    except Exception as exc:
        logger.error("Failed to add document %s to vector DB: %s", doc_id, exc)
        return False


def query_vector_db(question: str, user_role: str, n_results: int = 5) -> list[tuple[str, str, dict[str, Any]]]:
    if chromadb is None:
        logger.warning('chromadb not installed; QA search is disabled.')
        return []
    try:
        collection = get_collection()
        where_filter: dict[str, Any] = {"$and": [{"approved": 1}, {"is_active": 1}]}
        if user_role != "admin":
            where_filter["$and"].append({f"role_{user_role}": True})

        results = collection.query(query_texts=[question], n_results=n_results, where=where_filter)
        output: list[tuple[str, str, dict[str, Any]]] = []
        for index, document in enumerate(results.get("documents", [[]])[0]):
            metadata = results.get("metadatas", [[]])[0][index]
            output.append((metadata.get("doc_id", ""), document, metadata))
        return output
    except Exception as exc:
        logger.error("Failed to query vector DB: %s", exc)
        return []


def delete_from_vector_db(doc_id: str) -> bool:
    if chromadb is None:
        logger.warning('chromadb not installed; nothing to delete for %s.', doc_id)
        return True
    try:
        collection = get_collection()
        collection.delete(where={"doc_id": doc_id})
        return True
    except Exception as exc:
        logger.error("Failed to delete document %s from vector DB: %s", doc_id, exc)
        return False
