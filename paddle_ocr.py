
from paddleocr import PaddleOCR

# Initialize OCR engine once
ocr = PaddleOCR(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False
)

# Process image
results = ocr.predict("C:\\Users\\rabhs\\Downloads\\image.webp")

# Extract recognized text
for result in results:
    data = result.json

    if callable(data):
        data = data()

    ocr_data = data.get("res", data)

    for text in ocr_data.get("rec_texts", []):
        print(text)
