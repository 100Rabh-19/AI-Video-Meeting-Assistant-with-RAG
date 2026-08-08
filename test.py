import os
from utils.Audio_processor import download_youtube_audio, convert_to_wav, chunk_audio
from core.transcriber import transcribe_all


def test_full_pipeline(url: str):
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
    print("STEP 4: Transcribing Chunks with Whisper...")
    print("=" * 60)
    full_transcript = transcribe_all(chunks, translate=False)

    print("\n" + "=" * 60)
    print("Pipeline Completed Successfully!")
    print("=" * 60)
    return full_transcript


if __name__ == "__main__":
    test_url = "https://www.youtube.com/watch?v=J-JaGlLiU8k"
    test_full_pipeline(test_url)
