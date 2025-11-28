import os
import time
import whisper

# Paths relative to this file
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(CURRENT_DIR, "audio")
OUTPUT_DIR = os.path.join(CURRENT_DIR, "output")

# Whisper settings
MODEL_NAME = "small"   # you can change to "base", "medium", etc
LANGUAGE = None        # let Whisper auto detect. Set "fr" if you want French bias.


def ensure_output_folder():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created folder: {OUTPUT_DIR}")


def load_model():
    """
    Load Whisper model once and reuse it for all files.
    CPU only on your Asus (fp16 disabled later).
    """
    print(f"Loading Whisper model: {MODEL_NAME} (first time can take a bit)...")
    model = whisper.load_model(MODEL_NAME)
    print("Model loaded.")
    return model


def list_audio_files():
    """
    Return a list of audio file paths inside AUDIO_DIR.
    """
    if not os.path.exists(AUDIO_DIR):
        print(f"Audio folder does not exist: {AUDIO_DIR}")
        return []

    # Added ".webm" here
    exts = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".webm"}
    files = []

    for name in os.listdir(AUDIO_DIR):
        path = os.path.join(AUDIO_DIR, name)
        if not os.path.isfile(path):
            continue
        _, ext = os.path.splitext(name)
        if ext.lower() in exts:
            files.append(path)

    print(f"Found {len(files)} audio files in {AUDIO_DIR}.")
    return sorted(files)


def transcribe_file(model, audio_path: str):
    """
    Transcribe a single audio file with Whisper and return the text.
    """
    filename = os.path.basename(audio_path)
    print(f"\nTranscribing: {filename}")

    options = {
        "fp16": False,  # important on CPU or non CUDA
    }
    if LANGUAGE is not None:
        options["language"] = LANGUAGE
        options["task"] = "transcribe"

    result = model.transcribe(audio_path, **options)
    text = result.get("text", "").strip()
    return text


def save_transcript(video_id: str, text: str):
    """
    Save transcript text to output/<video_id>.txt
    """
    output_path = os.path.join(OUTPUT_DIR, f"{video_id}.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Saved transcript to {output_path}")


def main():
    ensure_output_folder()

    audio_files = list_audio_files()
    if not audio_files:
        print("No audio files found. Nothing to transcribe.")
        return

    model = load_model()

    for audio_path in audio_files:
        base = os.path.basename(audio_path)
        video_id, _ = os.path.splitext(base)

        output_path = os.path.join(OUTPUT_DIR, f"{video_id}.txt")
        if os.path.exists(output_path):
            print(f"Skipping {video_id} because transcript already exists.")
            continue

        try:
            text = transcribe_file(model, audio_path)
            if not text:
                print(f"Warning: got empty transcript for {video_id}.")
            save_transcript(video_id, text)
            time.sleep(0.5)
        except Exception as e:
            print(f"Error transcribing {video_id}: {e}")


if __name__ == "__main__":
    main()
