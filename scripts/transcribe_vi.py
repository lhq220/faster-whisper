import os
import sys
import json
from pathlib import Path
from faster_whisper import WhisperModel

audio_file = sys.argv[1]

if not os.path.isfile(audio_file):
    raise FileNotFoundError(f"Audio file not found: {audio_file}")

os.makedirs("output", exist_ok=True)

model = WhisperModel(
    "small",
    device="cpu",
    compute_type="int8"
)

segments, info = model.transcribe(
    audio_file,
    language="vi",
    beam_size=5,
    vad_filter=True
)

segments = list(segments)

audio_name = Path(audio_file).stem

txt_path = f"output/{audio_name}.txt"
json_path = f"output/{audio_name}.json"
srt_path = f"output/{audio_name}.srt"

with open(txt_path, "w", encoding="utf-8") as f:
    for segment in segments:
        f.write(segment.text.strip() + "\n")

data = {
    "language": info.language,
    "duration": info.duration,
    "segments": [
        {
            "start": s.start,
            "end": s.end,
            "text": s.text.strip()
        }
        for s in segments
    ]
}

with open(json_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

def format_srt_time(seconds):
    milliseconds = round(seconds * 1000)
    hours, remainder = divmod(milliseconds, 3600000)
    minutes, remainder = divmod(remainder, 60000)
    secs, ms = divmod(remainder, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{ms:03}"

with open(srt_path, "w", encoding="utf-8") as f:
    for index, segment in enumerate(segments, 1):
        f.write(f"{index}\n")
        f.write(
            f"{format_srt_time(segment.start)} --> "
            f"{format_srt_time(segment.end)}\n"
        )
        f.write(segment.text.strip() + "\n\n")

print("Transcription completed.")
print(f"Language: {info.language}")
print(f"Duration: {info.duration:.2f} seconds")
print(f"Output: {txt_path}, {srt_path}, {json_path}")
