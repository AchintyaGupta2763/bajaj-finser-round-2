from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import pytesseract
import cv2
import numpy as np
import io

app = FastAPI()

@app.post("/get-lab-tests")
async def get_lab_tests(file: UploadFile = File(...)):
    try:
        contents = await file.read()

        # Load image
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # --- Optimization: Resize ---
        height, width = img.shape[:2]
        if width > 1000:
            scaling_factor = 1000 / width
            img = cv2.resize(img, None, fx=scaling_factor, fy=scaling_factor, interpolation=cv2.INTER_AREA)

        # --- Optimization: Grayscale + Threshold ---
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, img = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

        # OCR with Tesseract
        custom_config = r'--oem 3 --psm 4'
        text = pytesseract.image_to_string(img, config=custom_config)

        text = text.replace('\n', ' ')  # Optional: flatten for better parsing

        # Extract lab tests
        lab_tests = parse_lab_report(text)

        return JSONResponse(content={
            "is_success": True,
            "data": lab_tests
        })
    except Exception as e:
        return JSONResponse(content={"is_success": False, "error": str(e)})

import re

def parse_lab_report(text):
    lab_tests = []

    # Improved flexible regex
    pattern = re.compile(
        r"(?P<test_name>[A-Za-z ()]+)[\s:]*"
        r"(?P<test_value>[\d.]+)[\s]*"
        r"(?P<unit>[a-zA-Z%/]+)?[\s]*"
        r"[\[\(]?(?P<ref_min>[\d.]+)\s*[-–]\s*(?P<ref_max>[\d.]+)[\]\)]?",
        re.IGNORECASE
    )

    for match in pattern.finditer(text):
        try:
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
        except:
            pass  # Ignore minor parsing errors safely

    return lab_tests
