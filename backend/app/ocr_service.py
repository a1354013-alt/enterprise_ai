"""OCR service for extracting text from images."""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger("knowledge_workspace")

try:
    import pytesseract
    from PIL import Image
    from PIL import ImageFile
    from PIL import UnidentifiedImageError
    from PIL import Image as PILImage

    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False
    logger.warning("pytesseract or PIL not installed. OCR functionality will be disabled.")

_OCR_ENABLED = os.getenv("OCR_ENABLED", "1").strip().lower() not in {"0", "false", "no", "off"}


def get_ocr_status() -> dict[str, Any]:
    return {
        "enabled": bool(_OCR_ENABLED),
        "available": bool(PYTESSERACT_AVAILABLE),
    }


def extract_text_from_image(image_path: str | Path) -> str:
    """
    Extract text from an image file using OCR.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Extracted text content, or empty string if OCR fails
    """
    if not _OCR_ENABLED:
        return ""
    if not PYTESSERACT_AVAILABLE:
        logger.info("OCR is not available. Install pytesseract and PIL for OCR support.")
        return ""

    try:
        image_path = Path(image_path)
        if not image_path.exists():
            logger.warning(f"Image file not found: {image_path}")
            return ""

        tesseract_cmd = os.getenv("OCR_TESSERACT_CMD", "").strip()
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

        ImageFile.LOAD_TRUNCATED_IMAGES = False
        PILImage.MAX_IMAGE_PIXELS = int(os.getenv("OCR_MAX_PIXELS", str(20_000_000)))

        # Open image with PIL
        with Image.open(image_path) as img:
            img.load()

            # Configure tesseract for better accuracy
            lang = os.getenv("OCR_LANG", "").strip()
            custom_config = os.getenv("OCR_TESSERACT_CONFIG", "").strip() or r"--oem 3 --psm 6"

            # Extract text
            text = pytesseract.image_to_string(img, config=custom_config, lang=lang or None)

            # Clean up the extracted text
            cleaned_text = " ".join((text or "").split())

        logger.info(f"Extracted {len(cleaned_text)} characters from {image_path.name}")
        return cleaned_text
    except (UnidentifiedImageError, OSError) as exc:
        logger.warning("OCR skipped for unreadable image %s: %s", image_path, exc)
        return ""
    except Exception as exc:
        logger.error(f"OCR failed for {image_path}: {exc}")
        return ""


def batch_extract_text(image_paths: list[str | Path]) -> dict[str, str]:
    """
    Extract text from multiple images.
    
    Args:
        image_paths: List of image file paths
        
    Returns:
        Dictionary mapping file paths to extracted text
    """
    results: dict[str, str] = {}
    for path in image_paths:
        path_str = str(path)
        results[path_str] = extract_text_from_image(path)
    return results
