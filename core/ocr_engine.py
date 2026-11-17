import os
from typing import List, Union

_ocr_instance = None


def get_ocr():
    """
    Lazy singleton loader for PaddleOCR engine.
    Ensures models are only loaded into memory once and reused across requests.
    """
    global _ocr_instance
    if _ocr_instance is None:
        print("[OCR] Initializing PaddleOCR engine...")
        from paddleocr import PaddleOCR
        _ocr_instance = PaddleOCR(
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False
        )
        print("[OCR] PaddleOCR engine ready.")
    return _ocr_instance


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif"}


def is_image_file(path_or_filename: str) -> bool:
    """Checks if the given file path or name has an image extension."""
    if not path_or_filename:
        return False
    ext = os.path.splitext(path_or_filename)[1].lower()
    return ext in IMAGE_EXTENSIONS


def extract_text_from_image(image_path: str) -> str:
    """
    Extracts text from a single image using PaddleOCR.
    
    :param image_path: Path to the image file on disk.
    :return: Extracted text as a clean multi-line string.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found at: {image_path}")

    ocr = get_ocr()
    results = ocr.predict(image_path)

    extracted_lines: List[str] = []

    for result in results:
        # PaddleOCR 3.x returns result objects with .json property or callable .json()
        data = getattr(result, "json", None)
        if callable(data):
            data = data()
        elif data is None:
            data = result

        if isinstance(data, dict):
            ocr_data = data.get("res", data)
            rec_texts = ocr_data.get("rec_texts", [])
            for text in rec_texts:
                if text and text.strip():
                    extracted_lines.append(text.strip())
        elif isinstance(data, list):
            # Fallback for alternative/legacy result formats: [[box, (text, score)], ...]
            for item in data:
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    text_info = item[1]
                    if isinstance(text_info, (list, tuple)) and len(text_info) >= 1:
                        txt = str(text_info[0]).strip()
                        if txt:
                            extracted_lines.append(txt)
                    elif isinstance(text_info, str) and text_info.strip():
                        extracted_lines.append(text_info.strip())

    return "\n".join(extracted_lines)


def extract_text_from_images(image_paths: List[str]) -> str:
    """
    Extracts and aggregates text from one or more images into a structured transcript.
    Useful for multi-page documents, presentations, or photo batches.
    """
    if not image_paths:
        return ""

    if len(image_paths) == 1:
        return extract_text_from_image(image_paths[0])

    combined_sections = []
    for idx, path in enumerate(image_paths, 1):
        filename = os.path.basename(path)
        print(f"[OCR] Processing page/image {idx}/{len(image_paths)}: {filename}")
        page_text = extract_text_from_image(path)
        if page_text.strip():
            combined_sections.append(f"--- [Page / Image {idx}: {filename}] ---\n{page_text}")
        else:
            combined_sections.append(f"--- [Page / Image {idx}: {filename}] ---\n(No readable text detected)")

    return "\n\n".join(combined_sections)
