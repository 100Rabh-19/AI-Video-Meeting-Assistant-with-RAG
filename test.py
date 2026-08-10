import os
from dotenv import load_dotenv
from utils.Audio_processor import download_youtube_audio, convert_to_wav, chunk_audio
from core.transcriber import transcribe_all

# Load environment variables from .env file (for Sarvam AI / Whisper settings)
load_dotenv()


def test_full_pipeline(url: str, language: str = "hinglish"):
    """
    Runs the full end-to-end pipeline:
    1. Downloads audio from YouTube.
    2. Converts raw audio to 16kHz mono WAV format.
    3. Splits audio into 5-minute chunks.
    4. Transcribes chunks using Sarvam AI (for 'hinglish') or Whisper (for 'english').
    """
    print("=" * 60)
    print("STEP 1: Downloading YouTube Audio...")
    print("=" * 60)
    raw_audio_path = download_youtube_audio(url)
    print(f"-> Raw Audio Downloaded: {raw_audio_path}")

    print("\n" + "=" * 60)
    print("STEP 2: Converting to 16kHz Mono WAV...")
    print("=" * 60)
    mono_audio_path = convert_to_wav(raw_audio_path, remove_original=True)
    print(f"-> Mono 16kHz Audio Saved: {mono_audio_path}")

    print("\n" + "=" * 60)
    print("STEP 3: Chunking Audio (5 min per chunk)...")
    print("=" * 60)
    chunks = chunk_audio(mono_audio_path, chunk_minutes=5)
    print(f"-> Created {len(chunks)} Chunks:")
    for idx, c in enumerate(chunks, 1):
        print(f"   Chunk {idx}: {c}")

    print("\n" + "=" * 60)
    engine_name = "Sarvam AI" if language.lower() == "hinglish" else "Whisper"
    print(f"STEP 4: Transcribing Chunks with {engine_name} (language='{language}')...")
    print("=" * 60)
    full_transcript = transcribe_all(chunks, language=language)

    print("\n" + "=" * 60)
    print("Pipeline Completed Successfully!")
    print("=" * 60)
    return full_transcript


if __name__ == "__main__":
    test_url = "https://www.youtube.com/watch?v=J-JaGlLiU8k"
    
    # Set language="hinglish" for Sarvam AI or language="english" for Whisper
    transcript = test_full_pipeline(test_url, language="hinglish")
    
    print("\n" + "=" * 60)
    print("FINAL TRANSCRIPT:")
    print("=" * 60)
    print(transcript)
    
    # Save transcript to file for easy viewing
    output_file = "transcript.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(transcript)
    print(f"\n-> Saved complete transcript to: {os.path.abspath(output_file)}")

