import whisper
import os

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")

_model = None


def load_model():
    global _model
    if _model is None:
        print(f"Loading Whisper model '{WHISPER_MODEL}'...")
        _model = whisper.load_model(WHISPER_MODEL)
    return _model


def transcribe_chunk(chunk_path: str, translate: bool = False) -> str:
    """Transcribes or translates a single audio chunk using Whisper."""
    model = load_model()
    task = "translate" if translate else "transcribe"
    result = model.transcribe(chunk_path, task=task)
    return result["text"].strip()


def transcribe_all(chunks: list[str], translate: bool = False) -> str:
    """Transcribes or translates all audio chunks and combines into a single transcript."""
    full_transcript = []
    for i, chunk in enumerate(chunks):
        print(f"Transcribing chunk {i + 1}/{len(chunks)}: {chunk}")
        text = transcribe_chunk(chunk, translate=translate)
        full_transcript.append(text)

    complete_text = "\n\n".join(full_transcript)
    print("\n--- Full Transcript ---")
    print(complete_text)
    return complete_text
