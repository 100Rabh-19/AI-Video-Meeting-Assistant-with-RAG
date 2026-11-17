import os
import shutil
from typing import Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from core.extractor import extract_transcript
from core.Summarize import summarize, get_title
from core.rag_engine import HybridRAG
from core.ocr_engine import (
    extract_text_from_image,
    extract_text_from_images,
    is_image_file,
    IMAGE_EXTENSIONS
)

# Load environment variables (.env)
load_dotenv()

# Workspace & Storage Configuration
DOWNLOAD_DIR = os.path.abspath("downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

import json

SESSION_FILE = os.path.join(DOWNLOAD_DIR, "active_session.json")

# Active Application Session State
active_state = {
    "title": None,
    "summary": None,
    "transcript": None,
    "rag_engine": None,
    "source": None,
    "language": "english"
}


def save_active_session(title: str, summary: str, transcript: str, source: str, language: str, rag_engine: HybridRAG):
    """Saves session state both in memory and on disk to persist across server reloads."""
    active_state["title"] = title
    active_state["summary"] = summary
    active_state["transcript"] = transcript
    active_state["rag_engine"] = rag_engine
    active_state["source"] = source
    active_state["language"] = language

    try:
        data = {
            "title": title,
            "summary": summary,
            "transcript": transcript,
            "source": source,
            "language": language
        }
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Session] Warning: failed saving active_session.json: {e}")


def restore_active_session_if_needed():
    """Auto-restores the RAG engine from disk cache if memory was cleared by a server reload."""
    if active_state.get("rag_engine") is not None:
        return active_state["rag_engine"]

    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            transcript = data.get("transcript")
            if transcript and transcript.strip():
                print(f"[Session] Auto-rebuilding Hybrid RAG engine from cached session: {data.get('source')}")
                active_state["title"] = data.get("title")
                active_state["summary"] = data.get("summary")
                active_state["transcript"] = transcript
                active_state["source"] = data.get("source")
                active_state["language"] = data.get("language")
                active_state["rag_engine"] = HybridRAG(transcript)
                return active_state["rag_engine"]
        except Exception as e:
            print(f"[Session] Error restoring session from disk: {e}")

    return None

app = FastAPI(
    title="AI Video Meeting Assistant with Hybrid RAG",
    description="FastAPI backend featuring YouTube audio extraction, local drag & drop, file system explorer, BM25 + Vector Hybrid Search RAG, and Conversational Chat Memory.",
    version="2.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Assets
static_dir = os.path.abspath("static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serves the main single-page application dashboard."""
    index_path = os.path.abspath(os.path.join("templates", "index.html"))
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail="Index template not found")
    return FileResponse(index_path)


@app.post("/api/process/yt")
async def process_youtube_link(payload: dict = Body(...)):
    """Processes a YouTube URL: downloads audio, transcribes, summarizes, and indexes for Hybrid RAG."""
    url = payload.get("url")
    language = payload.get("language", "english")
    
    if not url or not url.startswith("http"):
        raise HTTPException(status_code=400, detail="Invalid YouTube URL provided")

    try:
        print(f"\n[FastAPI] Processing YouTube URL: {url} (Language: {language})")
        transcript = extract_transcript(url, language=language)
        
        if not transcript.strip():
            raise HTTPException(status_code=422, detail="Extraction returned empty transcript.")

        title = get_title(transcript)
        summary_text = summarize(transcript)
        
        # Initialize Hybrid RAG (BM25 + Vector Search + Conversational Memory)
        rag_engine = HybridRAG(transcript)
        
        # Store and persist session state
        save_active_session(title, summary_text, transcript, url, language, rag_engine)

        word_count = len(transcript.split())

        return {
            "status": "success",
            "title": title,
            "summary": summary_text,
            "transcript": transcript,
            "word_count": word_count,
            "language": language,
            "source": url
        }
    except Exception as e:
        print(f"[Error] Failed processing YouTube link: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/process/upload")
async def process_drag_and_drop_upload(
    file: UploadFile = File(...),
    language: str = Form("english")
):
    """Processes a drag-and-drop file upload (Audio, Video, TXT, or Image for OCR)."""
    try:
        filename = file.filename
        file_path = os.path.join(DOWNLOAD_DIR, f"upload_{filename}")
        
        print(f"\n[FastAPI] Saving uploaded file to: {file_path}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        print(f"[FastAPI] Processing uploaded file: {filename}")
        
        if is_image_file(filename):
            print(f"[FastAPI] Detected Image. Running PaddleOCR on: {filename}")
            transcript = extract_text_from_image(file_path)
            processed_engine = "PaddleOCR (Image / Document)"
        elif filename.endswith(".txt"):
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                transcript = f.read()
            processed_engine = "Text Document"
        else:
            transcript = extract_transcript(file_path, language=language)
            processed_engine = f"Whisper ({language})"

        if not transcript.strip():
            raise HTTPException(status_code=422, detail="Content extraction returned empty text. Please ensure the file contains readable text or speech.")

        title = get_title(transcript)
        summary_text = summarize(transcript)
        
        rag_engine = HybridRAG(transcript)

        # Store and persist session state
        save_active_session(title, summary_text, transcript, filename, processed_engine, rag_engine)

        word_count = len(transcript.split())

        return {
            "status": "success",
            "title": title,
            "summary": summary_text,
            "transcript": transcript,
            "word_count": word_count,
            "language": processed_engine,
            "source": filename
        }
    except Exception as e:
        print(f"[Error] Failed processing file upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/process/images")
async def process_image_batch_upload(
    files: list[UploadFile] = File(...)
):
    """Processes multiple uploaded images using PaddleOCR, generates unified transcript and indexes into Hybrid RAG."""
    if not files:
        raise HTTPException(status_code=400, detail="No image files provided.")

    try:
        saved_paths = []
        file_names = []

        for f in files:
            if not is_image_file(f.filename):
                continue
            save_path = os.path.join(DOWNLOAD_DIR, f"ocr_{f.filename}")
            with open(save_path, "wb") as buffer:
                shutil.copyfileobj(f.file, buffer)
            saved_paths.append(save_path)
            file_names.append(f.filename)

        if not saved_paths:
            raise HTTPException(
                status_code=400,
                detail="No supported image files detected. Supported formats: PNG, JPG, JPEG, WEBP, BMP, TIFF."
            )

        print(f"\n[FastAPI] Processing {len(saved_paths)} images via PaddleOCR: {file_names}")
        transcript = extract_text_from_images(saved_paths)

        if not transcript.strip():
            raise HTTPException(status_code=422, detail="No readable text could be recognized from the uploaded images.")

        display_source = (
            file_names[0] if len(file_names) == 1
            else f"{len(file_names)} Images ({', '.join(file_names[:2])}{'...' if len(file_names) > 2 else ''})"
        )

        title = get_title(transcript)
        summary_text = summarize(transcript)
        rag_engine = HybridRAG(transcript)

        # Store and persist session state
        save_active_session(title, summary_text, transcript, display_source, "PaddleOCR (Multi-Image)", rag_engine)

        return {
            "status": "success",
            "title": title,
            "summary": summary_text,
            "transcript": transcript,
            "word_count": len(transcript.split()),
            "language": "PaddleOCR (Image Document)",
            "source": display_source
        }
    except Exception as e:
        print(f"[Error] Failed processing images: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/filesystem")
async def browse_file_system(path: Optional[str] = None):
    """Lists files and subdirectories for the Server File Explorer modal, including media and images."""
    try:
        target_dir = os.path.abspath(path) if path else os.getcwd()

        if not os.path.exists(target_dir) or not os.path.isdir(target_dir):
            target_dir = os.getcwd()

        parent_dir = os.path.dirname(target_dir) if target_dir != os.path.dirname(target_dir) else None

        items = []
        media_extensions = {".mp3", ".wav", ".m4a", ".mp4", ".mkv", ".flac", ".ogg", ".txt"}.union(IMAGE_EXTENSIONS)

        for entry in os.scandir(target_dir):
            if entry.name.startswith(".") or entry.name in ["__pycache__", "node_modules", ".venv", ".git"]:
                continue

            is_dir = entry.is_dir()
            ext = os.path.splitext(entry.name)[1].lower()
            is_media = is_dir or (ext in media_extensions)
            is_img = is_image_file(entry.name)

            size = entry.stat().st_size if not is_dir else 0

            items.append({
                "name": entry.name,
                "path": entry.path,
                "is_dir": is_dir,
                "is_media": is_media,
                "is_image": is_img,
                "size": size
            })

        # Sort: directories first, then files alphabetically
        items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))

        return {
            "current_path": target_dir,
            "parent_path": parent_dir,
            "items": items
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/process/filesystem")
async def process_file_system_item(payload: dict = Body(...)):
    """Processes a file selected directly from the local server file system (Audio, Video, TXT, or Image)."""
    file_path = payload.get("path")
    language = payload.get("language", "english")

    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Selected server file does not exist")

    try:
        print(f"\n[FastAPI] Processing File System item: {file_path}")
        
        if is_image_file(file_path):
            transcript = extract_text_from_image(file_path)
            engine_name = "PaddleOCR (Image Document)"
        elif file_path.endswith(".txt"):
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                transcript = f.read()
            engine_name = "Text Document"
        else:
            transcript = extract_transcript(file_path, language=language)
            engine_name = f"Whisper ({language})"

        if not transcript.strip():
            raise HTTPException(status_code=422, detail="Extracted transcript is empty.")

        title = get_title(transcript)
        summary_text = summarize(transcript)

        rag_engine = HybridRAG(transcript)

        # Store and persist session state
        save_active_session(title, summary_text, transcript, os.path.basename(file_path), engine_name, rag_engine)

        return {
            "status": "success",
            "title": title,
            "summary": summary_text,
            "transcript": transcript,
            "word_count": len(transcript.split()),
            "language": engine_name,
            "source": os.path.basename(file_path)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
async def chat_with_meeting_rag(payload: dict = Body(...)):
    """Conversational RAG Q&A endpoint featuring BM25 + Vector Search & Chat Memory."""
    question = payload.get("question")
    if not question or not question.strip():
        raise HTTPException(status_code=400, detail="Empty question provided")

    rag_engine: HybridRAG = restore_active_session_if_needed()
    if not rag_engine:
        raise HTTPException(
            status_code=400,
            detail="No meeting transcript has been processed yet. Please upload an image, audio, YouTube link, or file first."
        )

    try:
        answer = rag_engine.answer_question(question)
        return {
            "question": question,
            "answer": answer
        }
    except Exception as e:
        print(f"[Error] RAG Chat Exception: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/clear-memory")
async def clear_chat_memory():
    """Resets the conversational memory for the active RAG engine session."""
    rag_engine: HybridRAG = restore_active_session_if_needed()
    if rag_engine:
        rag_engine.clear_memory()
    return {"status": "cleared"}


@app.get("/api/session")
async def get_active_session():
    """Returns active or restored session state to prefill UI on page load or refresh."""
    restore_active_session_if_needed()
    if not active_state.get("transcript"):
        return {"active": False}
    return {
        "active": True,
        "title": active_state.get("title"),
        "summary": active_state.get("summary"),
        "transcript": active_state.get("transcript"),
        "word_count": len(active_state.get("transcript", "").split()),
        "language": active_state.get("language"),
        "source": active_state.get("source")
    }


if __name__ == "__main__":
    import uvicorn
    print("\n" + "=" * 60)
    print("[*] Starting AI Video Meeting Assistant Web Server on http://127.0.0.1:8000")
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=["core", "utils", "templates", "static"],
        reload_excludes=["downloads", "downloads/*", "*.wav", "*.mp3", "*.mp4", "*.m4a", "*.txt"]
    )
