#!/usr/bin/env python3
"""
ANSHUKA ETHER-BROADCAST (ईथर-प्रसारण) CLOUD RUNNER
Aman Tech Solutions (ATS Platform) & EtherComm Sovereign Content Engine

24/7 Independent Serverless Cloud Service on Render.com:
- Receives HTTP triggers from Cloudflare Worker
- Gemini 3.5 Flash Lite script generation
- Gemini 3.8 Flash Lite TTS emotional Hindi voice synthesis
- 1080p procedural visual compositing + animated audio waveform via FFmpeg
- Autonomous YouTube Data API v3 resumable upload
- Zero on-device dependency: runs 100% in the cloud
"""

import os
import json
import time
import base64
import subprocess
import requests
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from PIL import Image, ImageDraw, ImageFont

app = FastAPI(title="Anshuka EtherBroadcast Cloud Runner", version="1.0.0")

WIDTH_LANDSCAPE = 1920
HEIGHT_LANDSCAPE = 1080

BG_TOP = (10, 14, 23)
CARD_BG = (17, 24, 39)
CARD_BORDER = (31, 41, 55)
ACCENT_CYAN = (56, 189, 248)
ACCENT_EMERALD = (16, 185, 129)
ACCENT_GOLD = (250, 204, 21)
TEXT_WHITE = (255, 255, 255)
TEXT_MUTED = (156, 163, 175)

RECORDS_CACHE = []

class TriggerRequest(BaseModel):
    customTopic: Optional[str] = None
    platforms: Optional[List[str]] = ["youtube"]
    privacyStatus: Optional[str] = "unlisted"
    voicePersona: Optional[str] = "Puck"

def get_font(size, bold=False):
    candidate_paths = [
        "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in candidate_paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except:
                pass
    return ImageFont.load_default()

def wrap_text(text, font, max_width, draw):
    words = text.split()
    lines = []
    current_line = []
    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        w = bbox[2] - bbox[0]
        if w <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))
    return lines

def create_graphic_frame(title, subtitle, dialogue, out_png):
    im = Image.new("RGB", (WIDTH_LANDSCAPE, HEIGHT_LANDSCAPE), BG_TOP)
    draw = ImageDraw.Draw(im)

    # Top Header Bar
    draw.rectangle([0, 0, WIDTH_LANDSCAPE, 80], fill=(15, 23, 42))
    draw.line([0, 80, WIDTH_LANDSCAPE, 80], fill=CARD_BORDER, width=2)

    font_brand = get_font(26, bold=True)
    font_sub_brand = get_font(18, bold=True)
    draw.text((60, 24), "ईथर-प्रसारण", font=font_brand, fill=ACCENT_GOLD)
    draw.text((235, 28), "|   ETHER-BROADCAST  •  SOVEREIGN CLOUD STREAM", font=font_sub_brand, fill=ACCENT_CYAN)

    # Live Badge
    draw.rectangle([WIDTH_LANDSCAPE - 340, 18, WIDTH_LANDSCAPE - 40, 62], fill=(24, 32, 47), outline=CARD_BORDER)
    draw.ellipse([WIDTH_LANDSCAPE - 325, 34, WIDTH_LANDSCAPE - 313, 46], fill=(239, 68, 68))
    draw.text((WIDTH_LANDSCAPE - 300, 26), "ON-AIR  |  ATS PLATFORM", font=get_font(16, bold=True), fill=TEXT_WHITE)

    # Hero Content Card
    card_x1, card_y1, card_x2, card_y2 = 120, 120, WIDTH_LANDSCAPE - 120, 720
    draw.rectangle([card_x1, card_y1, card_x2, card_y2], fill=CARD_BG, outline=CARD_BORDER, width=2)
    draw.line([card_x1, card_y1, card_x2, card_y1], fill=ACCENT_CYAN, width=3)

    # Category Pill
    draw.rectangle([card_x1 + 40, card_y1 + 35, card_x1 + 420, card_y1 + 71], fill=(30, 41, 59), outline=ACCENT_EMERALD)
    draw.text((card_x1 + 55, card_y1 + 40), "★ सच्चाई की वेल्थ  |  सॉवरेन इंटेलिजेंस", font=get_font(16, bold=True), fill=ACCENT_EMERALD)

    # Title
    font_title = get_font(44, bold=True)
    title_lines = wrap_text(title, font_title, card_x2 - card_x1 - 80, draw)
    ty = card_y1 + 95
    for t_line in title_lines[:2]:
        draw.text((card_x1 + 40, ty), t_line, font=font_title, fill=TEXT_WHITE)
        ty += 58

    # Subtitle
    if subtitle:
        draw.text((card_x1 + 40, ty + 10), subtitle, font=get_font(24), fill=ACCENT_CYAN)
        ty += 45

    # Core Dialogue
    draw.line([card_x1 + 40, ty + 15, card_x2 - 40, ty + 15], fill=CARD_BORDER, width=1)
    ty += 35
    font_dialogue = get_font(22)
    dialogue_lines = wrap_text(f'"{dialogue}"', font_dialogue, card_x2 - card_x1 - 100, draw)
    for d_line in dialogue_lines[:4]:
        draw.text((card_x1 + 50, ty), d_line, font=font_dialogue, fill=TEXT_MUTED)
        ty += 34

    draw.text((card_x1 + 50, card_y2 - 45), "वक्ता: अमन कुमार (Aman Kumar) — संस्थापक, Aman Tech Solutions", font=get_font(18, bold=True), fill=ACCENT_GOLD)

    # Waveform Container Box
    wave_x1, wave_y1, wave_x2, wave_y2 = 120, 750, WIDTH_LANDSCAPE - 120, 980
    draw.rectangle([wave_x1, wave_y1, wave_x2, wave_y2], fill=(13, 19, 33), outline=CARD_BORDER, width=2)
    draw.text((wave_x1 + 30, wave_y1 + 15), "AUDIO WAVEFORM SPECTRUM  |  GEMINI EMOTIVE ENGINE", font=get_font(13, bold=True), fill=ACCENT_CYAN)

    # Footer
    draw.rectangle([0, HEIGHT_LANDSCAPE - 60, WIDTH_LANDSCAPE, HEIGHT_LANDSCAPE], fill=(15, 23, 42))
    draw.line([0, HEIGHT_LANDSCAPE - 60, WIDTH_LANDSCAPE, HEIGHT_LANDSCAPE - 60], fill=CARD_BORDER, width=2)
    draw.text((40, HEIGHT_LANDSCAPE - 42), "मंच: anshuka.in   •   Aman Tech Solutions (Proprietor: Aman Kumar)", font=get_font(16), fill=TEXT_MUTED)
    draw.text((WIDTH_LANDSCAPE - 450, HEIGHT_LANDSCAPE - 42), "EtherComm Sovereign Mesh Architecture", font=get_font(15, bold=True), fill=ACCENT_GOLD)

    im.save(out_png)
    return wave_x1 + 30, wave_y1 + 45, wave_x2 - wave_x1 - 60, wave_y2 - wave_y1 - 60

def generate_script(api_key, custom_topic):
    prompt = f"""You are the lead content architect for "ईथर-प्रसारण" (EtherBroadcast) by Aman Tech Solutions (Proprietor: Aman Kumar).
Ethos:
- Sovereign AI Agents and Autonomous Workflow Automation (ATS Platform, anshuka.in)
- EtherComm decentralized P2P mesh communication
- "सच्चाई की वेल्थ" (Wealth of Truth) ethos
{f'Target Topic: "{custom_topic}"' if custom_topic else 'Inspiring theme around autonomous computing, sovereign tech, or decentralized intelligence.'}

Generate a short, powerful, conversational broadcast monologue in natural, authentic Hindi.
Duration: 30 to 45 seconds of speech (approx. 50-70 words).

Output STRICT JSON:
{{
  "title": "Short Hindi title (max 7-9 words)",
  "subtitle": "अमन टेक सॉल्यूशंस ईथर-प्रसारण",
  "dialogue": "Spoken monologue in natural Hindi Devanagari script",
  "summary": "1-sentence summary",
  "tags": ["Aman Kumar", "ATS Platform", "EtherComm", "Sovereign AI"],
  "socialCaption": "Short engaging post caption with hashtags"
}}"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={api_key}"
    res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=15)
    if res.status_code != 200:
        raise RuntimeError(f"Script generation failed: {res.text}")
    data = res.json()
    text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
    if text.startswith("```json"):
        text = text[7:-3].strip()
    elif text.startswith("```"):
        text = text[3:-3].strip()
    return json.loads(text)

def synthesize_audio(api_key, text, voice="Puck"):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash-lite-tts:generateContent?key={api_key}"
    body = {
        "contents": [{"parts": [{"text": text}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {
                        "voiceName": voice
                    }
                }
            }
        }
    }
    res = requests.post(url, json=body, timeout=30)
    if res.status_code != 200:
        raise RuntimeError(f"TTS synthesis failed: {res.text}")
    data = res.json()
    part = data["candidates"][0]["content"]["parts"][0]
    raw_b64 = part["inlineData"]["data"]
    return base64.b64decode(raw_b64)

def get_youtube_token():
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN")
    if not (client_id and client_secret and refresh_token):
        return None
    res = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }, timeout=10)
    if res.status_code == 200:
        return res.json().get("access_token")
    return None

def upload_youtube_video(token, mp4_path, title, description, tags, privacy="unlisted"):
    metadata = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "28"
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False
        }
    }
    with open(mp4_path, "rb") as f:
        video_bytes = f.read()

    init_res = requests.post(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=UTF-8",
            "X-Upload-Content-Length": str(len(video_bytes)),
            "X-Upload-Content-Type": "video/mp4"
        },
        json=metadata,
        timeout=15
    )
    if init_res.status_code not in (200, 201):
        raise RuntimeError(f"YouTube upload init failed: {init_res.text}")

    upload_url = init_res.headers.get("location")
    upload_res = requests.put(
        upload_url,
        headers={
            "Content-Type": "video/mp4",
            "Content-Length": str(len(video_bytes))
        },
        data=video_bytes,
        timeout=180
    )
    if upload_res.status_code not in (200, 201):
        raise RuntimeError(f"YouTube upload transfer failed: {upload_res.text}")
    data = upload_res.json()
    vid = data.get("id")
    return {"videoId": vid, "url": f"https://youtube.com/watch?v={vid}"}

@app.get("/health")
def health():
    return {
        "status": "active",
        "service": "Anshuka EtherBroadcast 24/7 Cloud Runner",
        "ethos": "सच्चाई की वेल्थ — अमन टेक सॉल्यूशंस",
        "platform": "Render Serverless Cloud",
        "independentMode": True
    }

@app.get("/api/etherbroadcast/status")
def get_status():
    return {
        "success": True,
        "service": "EtherBroadcast Cloud Engine",
        "total": len(RECORDS_CACHE),
        "latest": RECORDS_CACHE[0] if RECORDS_CACHE else None,
        "history": RECORDS_CACHE
    }

@app.post("/api/etherbroadcast/trigger")
def trigger_broadcast(req: TriggerRequest):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not configured")

    broadcast_id = f"eb_cloud_{int(time.time())}"
    tmp_dir = "/tmp"
    audio_path = os.path.join(tmp_dir, f"{broadcast_id}.wav")
    bg_png = os.path.join(tmp_dir, f"{broadcast_id}_bg.png")
    mp4_path = os.path.join(tmp_dir, f"{broadcast_id}.mp4")

    # 1. Script
    script = generate_script(api_key, req.customTopic)

    # 2. Audio
    audio_bytes = synthesize_audio(api_key, script["dialogue"], req.voicePersona or "Puck")
    with open(audio_path, "wb") as f:
        f.write(audio_bytes)

    # 3. Procedural Graphics + FFmpeg
    wx, wy, ww, wh = create_graphic_frame(script["title"], script.get("subtitle", ""), script["dialogue"], bg_png)

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", bg_png,
        "-i", audio_path,
        "-filter_complex",
        f"[1:a]showwaves=s={ww}x{wh}:mode=cline:colors=0x38bdf8|0x10b981:rate=25[fg];"
        f"[0:v][fg]overlay=x={wx}:y={wy}:shortest=1[outv]",
        "-map", "[outv]",
        "-map", "1:a",
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-preset", "veryfast",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        mp4_path
    ]
    subprocess.run(ffmpeg_cmd, check=True)

    # 4. Dispatch
    publish_results = []
    if "youtube" in (req.platforms or []):
        yt_token = get_youtube_token()
        if yt_token:
            yt_res = upload_youtube_video(
                yt_token,
                mp4_path,
                script["title"],
                f"{script['dialogue']}\n\n{script.get('socialCaption', '')}\n\nआधिकारिक मंच: https://anshuka.in\nअमन टेक सॉल्यूशंस (ATS Platform) | ईथर-प्रसारण",
                script.get("tags", []),
                req.privacyStatus or "unlisted"
            )
            publish_results.append({
                "platform": "youtube",
                "success": True,
                "targetId": yt_res["videoId"],
                "url": yt_res["url"]
            })
        else:
            publish_results.append({
                "platform": "youtube",
                "success": False,
                "error": "No YouTube token configured in cloud environment"
            })

    record = {
        "id": broadcast_id,
        "script": script,
        "videoPath": mp4_path,
        "publishResults": publish_results,
        "status": "PUBLISHED" if any(r.get("success") for r in publish_results) else "FAILED",
        "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

    RECORDS_CACHE.insert(0, record)
    if len(RECORDS_CACHE) > 50:
        RECORDS_CACHE.pop()

    return {"success": True, "record": record}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
