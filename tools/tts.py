#!/usr/bin/env python3
"""Turn a plain-text listening script into an MP3.

Usage: make_audio.py SCRIPT.txt OUT.mp3

Uses Google Cloud Text-to-Speech when GOOGLE_TTS_API_KEY is set (natural voice),
otherwise the offline Festival HTS voice. Optional GOOGLE_TTS_VOICE overrides the
default voice (en-US-Chirp3-HD-Aoede, falling back to en-US-Neural2-F).
"""
import base64, json, os, re, subprocess, sys, tempfile, urllib.request

def chunks(text, limit=3800):
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    out, cur = [], ""
    for p in paras:
        while len(p) > limit:  # split very long paragraphs on sentences
            cut = p.rfind(". ", 0, limit) + 1 or limit
            out.append(p[:cut]); p = p[cut:].strip()
        if len(cur) + len(p) + 2 > limit and cur:
            out.append(cur); cur = p
        else:
            cur = (cur + "\n\n" + p) if cur else p
    if cur: out.append(cur)
    return out

def google(text, key, workdir):
    voices = [os.environ.get("GOOGLE_TTS_VOICE")] if os.environ.get("GOOGLE_TTS_VOICE") else ["en-US-Chirp3-HD-Aoede", "en-US-Neural2-F"]
    last = None
    for voice in voices:
        try:
            parts = []
            for i, c in enumerate(chunks(text)):
                body = json.dumps({"input": {"text": c},
                                   "voice": {"languageCode": "en-US", "name": voice},
                                   "audioConfig": {"audioEncoding": "MP3", "speakingRate": 1.05}}).encode()
                req = urllib.request.Request(f"https://texttospeech.googleapis.com/v1/text:synthesize?key={key}",
                                             data=body, headers={"Content-Type": "application/json"})
                audio = json.load(urllib.request.urlopen(req, timeout=120))["audioContent"]
                p = os.path.join(workdir, f"g{i:03d}.mp3"); open(p, "wb").write(base64.b64decode(audio)); parts.append(p)
            return parts, f"Google {voice}"
        except Exception as e:
            last = e
    raise RuntimeError(f"Google TTS failed: {last}")

def festival(text, workdir):
    parts = []
    for i, c in enumerate(chunks(text, 1500)):
        t = os.path.join(workdir, f"f{i:03d}.txt"); open(t, "w").write(c)
        w = os.path.join(workdir, f"f{i:03d}.wav")
        subprocess.run(["text2wave", "-eval", "(voice_cmu_us_slt_arctic_hts)", t, "-o", w], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        parts.append(w)
    return parts, "offline Festival voice"

def main(src, dst):
    text = open(src).read()
    with tempfile.TemporaryDirectory() as d:
        key = os.environ.get("GOOGLE_TTS_API_KEY")
        engine = None
        if key:
            try: parts, engine = google(text, key, d)
            except Exception as e: print(e, file=sys.stderr)
        if not engine: parts, engine = festival(text, d)
        lst = os.path.join(d, "list.txt")
        open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                        "-ac", "1", "-codec:a", "libmp3lame", "-b:a", "64k", dst], check=True)
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", dst],
                         capture_output=True, text=True).stdout.strip()
    print(f"wrote {dst} ({float(dur)/60:.1f} min) using {engine}")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
