#!/usr/bin/env python3
"""Batch vision review for rEFInd background candidates via Arena's OpenAI-compatible API."""
import base64
import io
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

import yaml
from PIL import Image

ROOT = Path(__file__).resolve().parent
CANDIDATES = ROOT / "candidates"
OUT = ROOT / "reviews" / "vision"
OUT.mkdir(parents=True, exist_ok=True)
KEY = yaml.safe_load(Path.home().joinpath(".dsh/.credentials.yaml").read_text())["refs"]["ARENA_API_API_KEY"]
URL = "https://api.arena.ai/v1/chat/completions"
HEADERS = {
    "Authorization": "Bearer " + KEY,
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/132.0 Safari/537.36",
    "Accept": "application/json",
}
PROMPT = """rEFIndの起動画面背景として審査してください。メニューは画面中央±20%、上から45〜62%の帯に固定表示されます。次のJSONだけを返してください。
{
  "summary": "何が描かれているかを日本語1文で",
  "face_position": "主要キャラの顔の位置を画像中の%で",
  "central_band": "中央帯にあるものを具体的に",
  "overlap": "none または partial または face",
  "fit": 0から10の整数,
  "beauty": 0から10の整数,
  "vibe": 0から10の整数,
  "quality": "2560x1440へ拡大した場合の画質評価を日本語で簡潔に",
  "text": "画像内の大きな文字やロゴの内容と位置。なければなし",
  "nsfw": "なし または注意内容"
}
overlapの意味: none=顔にも重要要素にも被らない、partial=一部接触する、face=顔に被る。fitは配置適合性、beautyはキャラの映え、vibeはパステル調の可愛い起動画面との一致度です。推測は推測と書いてください。"""


def image_data_url(path: Path) -> str:
    im = Image.open(path).convert("RGB")
    im.thumbnail((960, 540), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def review(path: Path) -> dict:
    payload = {
        "model": "gemini-3.8-flash",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": PROMPT},
                {"type": "image_url", "image_url": {"url": image_data_url(path)}},
            ],
        }],
        "max_tokens": 2500,
    }
    req = urllib.request.Request(URL, data=json.dumps(payload).encode(), headers=HEADERS)
    with urllib.request.urlopen(req, timeout=150) as response:
        data = json.load(response)
    choice = data["choices"][0]
    text = choice["message"]["content"]
    try:
        parsed = json.loads(text[text.index("{"):text.rindex("}") + 1])
    except Exception:
        parsed = {"parse_error": True, "raw": text}
    return {"file": path.name, "finish_reason": choice.get("finish_reason"), "review": parsed}


def main() -> None:
    files = sorted(CANDIDATES.glob("*.png")) + sorted(CANDIDATES.glob("*.jpg"))
    for index, path in enumerate(files, 1):
        dest = OUT / (path.stem + ".json")
        if dest.exists():
            previous = json.loads(dest.read_text())
            if "error" not in previous:
                print(f"[{index}/{len(files)}] skip {path.name}", flush=True)
                continue
        for attempt in range(3):
            try:
                result = review(path)
                dest.write_text(json.dumps(result, ensure_ascii=False, indent=2))
                r = result["review"]
                print(f"[{index}/{len(files)}] {path.name}: fit={r.get('fit')} vibe={r.get('vibe')} overlap={r.get('overlap')}", flush=True)
                break
            except urllib.error.HTTPError as exc:
                body = exc.read().decode()[:500]
                print(f"[{index}/{len(files)}] {path.name}: HTTP {exc.code} attempt {attempt + 1}: {body}", flush=True)
                if attempt == 2:
                    dest.write_text(json.dumps({"file": path.name, "error": f"HTTP {exc.code}", "body": body}, ensure_ascii=False, indent=2))
                else:
                    time.sleep(30 * (attempt + 1))
            except Exception as exc:
                print(f"[{index}/{len(files)}] {path.name}: {type(exc).__name__}: {exc}", flush=True)
                if attempt == 2:
                    dest.write_text(json.dumps({"file": path.name, "error": str(exc)}, ensure_ascii=False, indent=2))
                else:
                    time.sleep(30 * (attempt + 1))
        time.sleep(12)


if __name__ == "__main__":
    main()
