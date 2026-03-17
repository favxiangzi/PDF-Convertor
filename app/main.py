import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.pdf_processor import PDFProcessor

app = FastAPI(title="PDF Translation Tool for Garment Production Files")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# API routes first
@app.get("/")
async def read_root():
    return FileResponse("app/static/index.html")


@app.post("/translate")
async def translate_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    input_path = UPLOAD_DIR / file.filename
    output_filename = f"translated_{file.filename}"
    output_path = OUTPUT_DIR / output_filename

    try:
        content = await file.read()
        with open(input_path, "wb") as f:
            f.write(content)

        processor = PDFProcessor()
        result = processor.process_pdf(input_path, output_path)

        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "Processing failed"))

        return JSONResponse({
            "success": True,
            "output_file": output_filename,
            "pages_processed": result.get("pages_processed", 0),
            "pages_translated": result.get("pages_translated", 0),
            "message": f"Successfully translated {result.get('pages_translated', 0)} out of {result.get('pages_processed', 0)} pages"
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if input_path.exists():
            input_path.unlink()


@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="application/pdf", filename=filename)


# Static files mounted last
app.mount("/static", StaticFiles(directory="app/static"), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)