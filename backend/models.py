from pydantic import BaseModel, Field
from typing import List, Optional

# ============ 請求/回應模型 ============

# 【修正 #4】模型定義註解：
# 下列是實際 API 回傳的結構：
# - /api/docs（一般使用者）：
#   id, filename, file_size, uploaded_at, approved, is_active, uploaded_by, allowed_roles
# - /api/admin/docs（admin）：
#   id, filename, file_size, uploaded_at, approved, is_active, uploaded_by, allowed_roles
# 【改進 #5】不回傳 saved_filename（內部檔名，不必暗露）

class QARequest(BaseModel):
    """問答請求"""
    question: str = Field(description="問題")
    # 注意：使用者角色由 JWT token 決定，不由 request body 提供

class Source(BaseModel):
    """引用來源"""
    doc_name: str = Field(description="文件名稱")
    chunk_text: str = Field(description="文本片段")
    page_or_section: str = Field(description="頁碼或段落")

class QAResponse(BaseModel):
    """問答回應"""
    answer: str = Field(description="回答")
    sources: List[Source] = Field(default=[], description="引用來源")

class GenerateRequest(BaseModel):
    """表單生成請求"""
    template_type: str = Field(description="模板類型")
    inputs: dict = Field(description="表單輸入")
    # 注意：使用者角色由 JWT token 決定，不由 request body 提供

class GenerateResponse(BaseModel):
    """表單生成回應"""
    content: str = Field(description="生成的內容")

# 【修正 #4】【簡化】移除未使用的 DocumentRecord
# 原因：這個類定義已經不符合實際 API 的回傳結構
# 且整個專案已經不依賴它，保留只會造成維護困擾
# 殘留的 QARequest, QAResponse, GenerateRequest, GenerateResponse 是實際使用的
