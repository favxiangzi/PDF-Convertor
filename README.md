# PDF Translation Tool for Garment Production Files

A web-based tool that translates English PDF pages containing "comment" or "comments" to Simplified Chinese.

## Features

- 🔍 Detects pages containing "comment" or "comments" (case-insensitive)
- 🌐 Translates English to Simplified Chinese
- 🔴 Adds Chinese translation in RED beside original text
- 📐 Preserves original layout, tables, and graphics
- 📄 Keeps same page count

## Requirements

- Python 3.10+
- macOS (for Chinese font support)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start the server:
```bash
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Usage

1. Open http://localhost:8000 in your browser
2. Drag & drop a PDF file
3. Click "Translate PDF"
4. Download the translated PDF

## Running in Background

```bash
# macOS/Linux
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &

# To stop the server
pkill -f "uvicorn"
```

## Notes

- Only pages containing "comment" or "comments" will be translated
- Chinese translations appear in RED on the right side of each line
- Original English text is preserved
