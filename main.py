from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import easyocr
import re
import io
from PIL import Image
import pytesseract
import cv2
import numpy as np

app = FastAPI()

# CPU-only EasyOCR
reader = easyocr.Reader(['en'], gpu=False)

@app.post("/get-lab-tests")
async def get_lab_tests(file: UploadFile = File(...)):
    try:
        contents = await file.read()

        # Open image
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Tesseract OCR
        custom_config = r'--oem 3 --psm 6'  # Best config for structured text
        text = pytesseract.image_to_string(img, config=custom_config)

        text = text.replace('\n', ' ')  # (Optional) flatten lines

        lab_tests = parse_lab_report(text)

        return JSONResponse(content={
            "is_success": True,
            "data": lab_tests
        })
    except Exception as e:
        return JSONResponse(content={"is_success": False, "error": str(e)})

def parse_lab_report(text):
    lab_tests = []
    pattern = re.compile(r"(?P<test_name>[\w\s\(\)]+)\s+(?P<test_value>[\d.]+)\s*(?P<unit>[%a-zA-Z/]+)?\s+\[(?P<ref_min>[\d.]+)-(?P<ref_max>[\d.]+)\]", re.IGNORECASE)

    for match in pattern.finditer(text):
        test_name = match.group("test_name").strip()
        test_value = float(match.group("test_value"))
        unit = match.group("unit") or ""
        ref_min = float(match.group("ref_min"))
        ref_max = float(match.group("ref_max"))

        lab_tests.append({
            "test_name": test_name,
            "test_value": str(test_value),
            "bio_reference_range": f"{ref_min}-{ref_max}",
            "test_unit": unit,
            "lab_test_out_of_range": not (ref_min <= test_value <= ref_max)
        })

    return lab_tests
