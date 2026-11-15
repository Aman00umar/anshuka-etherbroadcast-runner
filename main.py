#!/usr/bin/env python3
"""
ANSHUKA ETHER-BROADCAST (ईथर-प्रसारण) MULTI-SCENE CLOUD RUNNER
Aman Tech Solutions (ATS Platform) & EtherComm Sovereign Content Engine

24/7 Independent Serverless Cloud Service on Render.com:
- Receives HTTP triggers from Cloudflare Worker or autonomous cron
- Gemini 3.5 Flash Lite script generation with 3-scene narrative structure
- Gemini 3.8 Flash Lite TTS emotional Hindi voice synthesis
- Procedural multi-scene visual cards + dynamic slide transitions
- Continuous animated live audio waveform spectrum via FFmpeg
- Autonomous cross-publishing: YouTube Data API v3, Facebook Page Video, Instagram Reels
- Zero on-device dependency: runs 100% in the cloud within 512MB RAM
"""

import os
import json
import time
import base64
import wave
import subprocess
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from PIL import Image, ImageDraw, ImageFont

app = FastAPI(title="Anshuka EtherBroadcast Multi-Scene Cloud Runner", version="2.0.0")

WIDTH_LANDSCAPE = 1280
HEIGHT_LANDSCAPE = 720

BG_TOP = (10, 14, 23)
CARD_BG = (17, 24, 39)
CARD_BORDER = (31, 41, 55)
ACCENT_CYAN = (56, 189, 248)
ACCENT_EMERALD = (16, 185, 129)
ACCENT_GOLD = (250, 204, 21)
ACCENT_RED = (239, 68, 68)
TEXT_WHITE = (255, 255, 255)
TEXT_MUTED = (156, 163, 175)

ACCENT_PALETTE = {
    "gold": ACCENT_GOLD,
    "cyan": ACCENT_CYAN,
    "emerald": ACCENT_EMERALD,
    "red": ACCENT_RED,
}

RECORDS_CACHE = []

class TriggerRequest(BaseModel):
    customTopic: Optional[str] = None
    platforms: Optional[List[str]] = ["youtube", "facebook", "instagram"]
    privacyStatus: Optional[str] = "unlisted"
    voicePersona: Optional[str] = "Puck"

def get_font_hi(size, bold=False):
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

def get_font_en(size, bold=False):
    candidate_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
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

def create_scene_frame(scene, scene_idx, total_scenes, title, subtitle, out_png):
    im = Image.new("RGB", (WIDTH_LANDSCAPE, HEIGHT_LANDSCAPE), BG_TOP)
    draw = ImageDraw.Draw(im)

    accent_key = str(scene.get("accent", "")).lower()
    accent_color = ACCENT_PALETTE.get(accent_key, ACCENT_CYAN)

    # Top Header Bar
    draw.rectangle([0, 0, WIDTH_LANDSCAPE, 56], fill=(15, 23, 42))
    draw.line([0, 56, WIDTH_LANDSCAPE, 56], fill=CARD_BORDER, width=2)

    font_brand = get_font_hi(20, bold=True)
    font_sub_brand = get_font_en(13, bold=True)
    draw.text((40, 16), "ईथर-प्रसारण", font=font_brand, fill=ACCENT_GOLD)
    draw.text((170, 19), f"|   ETHER-BROADCAST  •  SCENE {scene_idx + 1}/{total_scenes}", font=font_sub_brand, fill=ACCENT_CYAN)

    # Live Badge with scene accent
    draw.rectangle([WIDTH_LANDSCAPE - 270, 12, WIDTH_LANDSCAPE - 30, 44], fill=(24, 32, 47), outline=CARD_BORDER)
    draw.ellipse([WIDTH_LANDSCAPE - 258, 24, WIDTH_LANDSCAPE - 248, 34], fill=accent_color)
    draw.text((WIDTH_LANDSCAPE - 238, 18), "ON-AIR  |  ATS PLATFORM", font=get_font_en(12, bold=True), fill=TEXT_WHITE)

    # Hero Content Card
    card_x1, card_y1, card_x2, card_y2 = 80, 80, WIDTH_LANDSCAPE - 80, 480
    draw.rectangle([card_x1, card_y1, card_x2, card_y2], fill=CARD_BG, outline=CARD_BORDER, width=2)
    draw.line([card_x1, card_y1, card_x2, card_y1], fill=accent_color, width=4)

    # Category Pill
    pill_tag = scene.get("tag", f"भाग {scene_idx + 1}")
    draw.rectangle([card_x1 + 30, card_y1 + 25, card_x1 + 340, card_y1 + 55], fill=(30, 41, 59), outline=accent_color)
    draw.text((card_x1 + 42, card_y1 + 30), f"★ {pill_tag}", font=get_font_hi(13, bold=True), fill=accent_color)

    # Scene Heading
    font_heading = get_font_hi(26, bold=True)
    h_lines = wrap_text(scene.get("heading", title), font_heading, card_x2 - card_x1 - 60, draw)
    ty = card_y1 + 75
    for hl in h_lines[:2]:
        draw.text((card_x1 + 30, ty), hl, font=font_heading, fill=TEXT_WHITE)
        ty += 36

    # Series Subtitle
    sub_text = f"{title}  •  {subtitle}" if subtitle else title
    draw.text((card_x1 + 30, ty + 6), sub_text, font=get_font_hi(15), fill=ACCENT_CYAN)
    ty += 30

    draw.line([card_x1 + 30, ty + 10, card_x2 - 30, ty + 10], fill=CARD_BORDER, width=1)
    ty += 24

    # Bullet Points with styled colored bullets
    points = scene.get("points", [])
    font_pt = get_font_hi(18)
    for pt in points[:3]:
        draw.ellipse([card_x1 + 35, ty + 6, card_x1 + 45, ty + 16], fill=accent_color)
        pt_lines = wrap_text(pt, font_pt, card_x2 - card_x1 - 90, draw)
        for pl in pt_lines:
            draw.text((card_x1 + 55, ty), pl, font=font_pt, fill=TEXT_MUTED)
            ty += 26
        ty += 8

    draw.text((card_x1 + 35, card_y2 - 35), "वक्ता: अमन कुमार (Aman Kumar) — संस्थापक, Aman Tech Solutions", font=get_font_hi(13, bold=True), fill=ACCENT_GOLD)

    # Waveform Container Box
    wave_x1, wave_y1, wave_x2, wave_y2 = 80, 505, WIDTH_LANDSCAPE - 80, 660
    draw.rectangle([wave_x1, wave_y1, wave_x2, wave_y2], fill=(13, 19, 33), outline=CARD_BORDER, width=2)
    draw.text((wave_x1 + 25, wave_y1 + 10), "AUDIO WAVEFORM SPECTRUM  |  GEMINI EMOTIVE ENGINE", font=get_font_en(11, bold=True), fill=ACCENT_CYAN)

    # Footer
    draw.rectangle([0, HEIGHT_LANDSCAPE - 45, WIDTH_LANDSCAPE, HEIGHT_LANDSCAPE], fill=(15, 23, 42))
    draw.line([0, HEIGHT_LANDSCAPE - 45, WIDTH_LANDSCAPE, HEIGHT_LANDSCAPE - 45], fill=CARD_BORDER, width=1)
    draw.text((30, HEIGHT_LANDSCAPE - 30), "मंच: anshuka.in   •   Aman Tech Solutions (Proprietor: Aman Kumar)", font=get_font_hi(12), fill=TEXT_MUTED)
    draw.text((WIDTH_LANDSCAPE - 330, HEIGHT_LANDSCAPE - 30), "EtherComm Sovereign Mesh Architecture", font=get_font_en(11, bold=True), fill=ACCENT_GOLD)

    im.save(out_png)
    even_w = ((wave_x2 - wave_x1 - 40) // 2) * 2
    even_h = ((wave_y2 - wave_y1 - 44) // 2) * 2
    return wave_x1 + 20, wave_y1 + 32, even_w, even_h

def generate_script(api_key, custom_topic):
    prompt = f"""You are the lead content architect for "ईथर-प्रसारण" (EtherBroadcast) by Aman Tech Solutions (Proprietor: Aman Kumar).
Ethos:
- Sovereign AI Agents and Autonomous Workflow Automation (ATS Platform, anshuka.in)
- EtherComm decentralized P2P mesh communication
- "सच्चाई की वेल्थ" (Wealth of Truth) ethos
{f'Target Topic: "{custom_topic}"' if custom_topic else 'Inspiring theme around autonomous computing, sovereign tech, or decentralized intelligence.'}

Generate a short, powerful, conversational broadcast monologue in natural, authentic Hindi.
Duration: 30 to 45 seconds of speech (approx. 50-70 words).

Structure the broadcast into 3 visual scenes:
1. Scene 1 (The Hook & Challenge / समस्या या पृष्ठभूमि): Intriguing opening question or reality check.
2. Scene 2 (The Sovereign Solution / सॉवरेन तकनीक व समाधान): ATS Platform, EtherComm, Sovereign AI.
3. Scene 3 (The Sovereign Ethos & Call-to-action / सच्चाई की वेल्थ व आह्वान): anshuka.in and digital sovereignty.

Output STRICT JSON:
{{
  "title": "Short Hindi title (max 7-9 words)",
  "subtitle": "अमन टेक सॉल्यूशंस ईथर-प्रसारण",
  "dialogue": "Continuous spoken monologue in natural Hindi Devanagari script for TTS voice",
  "summary": "1-sentence summary",
  "tags": ["Aman Kumar", "ATS Platform", "EtherComm", "Sovereign AI", "सच्चाई की वेल्थ"],
  "socialCaption": "Short engaging post caption with hashtags for YouTube/Facebook/Instagram",
  "scenes": [
    {{
      "tag": "भाग १: पृष्ठभूमि और समस्या",
      "heading": "Catchy Scene 1 Title in Hindi (max 5-7 words)",
      "points": ["Short punchy highlight 1", "Short punchy highlight 2"],
      "accent": "gold"
    }},
    {{
      "tag": "भाग २: सॉवरेन समाधान",
      "heading": "Catchy Scene 2 Title in Hindi (max 5-7 words)",
      "points": ["Short punchy highlight 1", "Short punchy highlight 2"],
      "accent": "cyan"
    }},
    {{
      "tag": "भाग ३: सच्चाई की वेल्थ",
      "heading": "Catchy Scene 3 Title in Hindi (max 5-7 words)",
      "points": ["Short punchy highlight 1", "Short punchy highlight 2"],
      "accent": "emerald"
    }}
  ]
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
    
    parsed = json.loads(text)
    
    # Safe fallback if scenes array is missing
    if "scenes" not in parsed or not isinstance(parsed["scenes"], list) or len(parsed["scenes"]) == 0:
        parsed["scenes"] = [
            {
                "tag": "भाग १: समस्या व परिप्रेक्ष्य",
                "heading": parsed.get("title", "सॉवरेन इंटेलिजेंस का आह्वान"),
                "points": ["केंद्रीकृत डेटा नियंत्रण की सीमाएं", "स्वायत्तता और गोपनीयता का महत्व"],
                "accent": "gold"
            },
            {
                "tag": "भाग २: सॉवरेन तकनीक",
                "heading": "एटीएस प्लेटफॉर्म और ईथरकॉम",
                "points": ["P2P मेश संचार नेटवर्क", "24/7 स्वतंत्र क्लाउड ऑटोनॉमी"],
                "accent": "cyan"
            },
            {
                "tag": "भाग ३: सच्चाई की वेल्थ",
                "heading": "डिजिटल संप्रभुता — anshuka.in",
                "points": ["सच्चाई पर आधारित स्वायत्त भविष्य", "जुड़िए आधिकारिक मंच anshuka.in से"],
                "accent": "emerald"
            }
        ]
    return parsed

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

def publish_facebook_video(page_token, page_id, mp4_path, title, description):
    with open(mp4_path, "rb") as f:
        res = requests.post(
            f"https://graph.facebook.com/v21.0/{page_id}/videos",
            data={
                "access_token": page_token,
                "title": title,
                "description": description,
            },
            files={"source": f},
            timeout=180
        )
    if res.status_code in (200, 201):
        data = res.json()
        vid = data.get("id")
        return {"success": True, "targetId": vid, "url": f"https://www.facebook.com/{page_id}/videos/{vid}"}
    return {"success": False, "error": res.text}

def publish_instagram_reel(token, ig_user_id, public_video_url, caption):
    # Step 1: Create IG Reels Media Container
    init_res = requests.post(
        f"https://graph.facebook.com/v21.0/{ig_user_id}/media",
        data={
            "access_token": token,
            "media_type": "REELS",
            "video_url": public_video_url,
            "caption": caption
        },
        timeout=30
    )
    if init_res.status_code not in (200, 201):
        return {"success": False, "error": f"Container creation failed: {init_res.text}"}
    
    creation_id = init_res.json().get("id")

    # Step 2: Poll container status until FINISHED
    for _ in range(12):
        time.sleep(6)
        st_res = requests.get(
            f"https://graph.facebook.com/v21.0/{creation_id}",
            params={"access_token": token, "fields": "status_code"},
            timeout=10
        )
        if st_res.status_code == 200:
            st = st_res.json().get("status_code")
            if st == "FINISHED":
                break
            elif st == "ERROR":
                return {"success": False, "error": "Instagram video processing failed"}

    # Step 3: Publish container
    pub_res = requests.post(
        f"https://graph.facebook.com/v21.0/{ig_user_id}/media_publish",
        data={
            "access_token": token,
            "creation_id": creation_id
        },
        timeout=30
    )
    if pub_res.status_code in (200, 201):
        pid = pub_res.json().get("id")
        permalink = f"https://www.instagram.com/reel/{pid}"
        try:
            p_res = requests.get(f"https://graph.facebook.com/v21.0/{pid}?fields=permalink&access_token={token}", timeout=10)
            if p_res.status_code == 200 and p_res.json().get("permalink"):
                permalink = p_res.json().get("permalink")
        except:
            pass
        return {"success": True, "targetId": pid, "url": permalink}
    return {"success": False, "error": f"Publish failed: {pub_res.text}"}

@app.get("/health")
def health():
    return {
        "status": "active",
        "service": "Anshuka EtherBroadcast 24/7 Cloud Runner (Multi-Scene)",
        "ethos": "सच्चाई की वेल्थ — अमन टेक सॉल्यूशंस",
        "platform": "Render Serverless Cloud",
        "independentMode": True,
        "multiSceneEnabled": True
    }

@app.get("/media/{filename}")
def serve_media(filename: str):
    file_path = os.path.join("/tmp", filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="video/mp4")
    raise HTTPException(status_code=404, detail="File not found")

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
    mp4_path = os.path.join(tmp_dir, f"{broadcast_id}.mp4")

    # 1. Multi-Scene Script Generation
    script = generate_script(api_key, req.customTopic)

    # 2. Emotive Audio Synthesis
    audio_bytes = synthesize_audio(api_key, script["dialogue"], req.voicePersona or "Puck")
    with open(audio_path, "wb") as f:
        f.write(audio_bytes)

    # Calculate exact duration
    with wave.open(audio_path, "r") as wf:
        total_duration = wf.getnframes() / float(wf.getframerate())

    # 3. Procedural Multi-Scene Graphics + Animated Waveform
    scenes = script.get("scenes", [])
    num_scenes = max(1, len(scenes))
    scene_duration = total_duration / num_scenes

    scene_images = []
    wx, wy, ww, wh = 100, 537, 1080, 110
    for idx, sc in enumerate(scenes):
        sc_png = os.path.join(tmp_dir, f"{broadcast_id}_scene_{idx}.png")
        wx, wy, ww, wh = create_scene_frame(sc, idx, num_scenes, script["title"], script.get("subtitle", ""), sc_png)
        scene_images.append(sc_png)

    # Write concat playlist for sequential visual scene transitions
    concat_txt = os.path.join(tmp_dir, f"{broadcast_id}_concat.txt")
    with open(concat_txt, "w") as f:
        for idx, sc_img in enumerate(scene_images):
            dur = scene_duration if idx < num_scenes - 1 else max(1.0, total_duration - (num_scenes - 1) * scene_duration)
            f.write(f"file '{sc_img}'\n")
            f.write(f"duration {dur:.3f}\n")
        f.write(f"file '{scene_images[-1]}'\n")

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-threads", "1",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_txt,
        "-i", audio_path,
        "-filter_complex",
        f"[1:a]showwaves=s={ww}x{wh}:mode=cline:colors=0x38bdf8|0x10b981:rate=25[fg];"
        f"[0:v][fg]overlay=x={wx}:y={wy}:shortest=1[outv]",
        "-map", "[outv]",
        "-map", "1:a",
        "-c:v", "libx264",
        "-threads", "1",
        "-tune", "stillimage",
        "-preset", "ultrafast",
        "-c:a", "aac",
        "-b:a", "128k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        mp4_path
    ]
    subprocess.run(ffmpeg_cmd, check=True)

    public_video_url = f"https://anshuka-etherbroadcast.onrender.com/media/{broadcast_id}.mp4"

    # 4. Multi-Platform Autonomous Dispatch
    publish_results = []
    target_platforms = req.platforms or ["youtube"]

    # 4a. YouTube
    if "youtube" in target_platforms:
        yt_token = get_youtube_token()
        if yt_token:
            try:
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
            except Exception as e:
                publish_results.append({
                    "platform": "youtube",
                    "success": False,
                    "error": str(e)
                })
        else:
            publish_results.append({
                "platform": "youtube",
                "success": False,
                "error": "No YouTube token configured in cloud environment"
            })

    # 4b. Facebook Page Video
    if "facebook" in target_platforms:
        page_token = os.environ.get("META_PAGE_ACCESS_TOKEN")
        page_id = os.environ.get("FACEBOOK_PAGE_ID", "984918738043473")
        if page_token and page_id:
            try:
                fb_desc = f"{script['title']}\n\n{script['dialogue']}\n\n{script.get('socialCaption', '')}\n\nमंच: https://anshuka.in | अमन टेक सॉल्यूशंस (सच्चाई की वेल्थ)"
                fb_res = publish_facebook_video(page_token, page_id, mp4_path, script["title"], fb_desc)
                publish_results.append({
                    "platform": "facebook",
                    "success": fb_res.get("success", False),
                    "targetId": fb_res.get("targetId"),
                    "url": fb_res.get("url"),
                    "error": fb_res.get("error")
                })
            except Exception as e:
                publish_results.append({
                    "platform": "facebook",
                    "success": False,
                    "error": str(e)
                })
        else:
            publish_results.append({
                "platform": "facebook",
                "success": False,
                "error": "META_PAGE_ACCESS_TOKEN or FACEBOOK_PAGE_ID not configured"
            })

    # 4c. Instagram Reel
    if "instagram" in target_platforms:
        page_token = os.environ.get("META_PAGE_ACCESS_TOKEN")
        ig_user_id = os.environ.get("INSTAGRAM_ACCOUNT_ID", "17841446842624563")
        if page_token and ig_user_id:
            try:
                ig_caption = f"{script['title']}\n\n{script.get('socialCaption', '')}\n\nसच्चाई की वेल्थ — अमन टेक सॉल्यूशंस • anshuka.in"
                ig_res = publish_instagram_reel(page_token, ig_user_id, public_video_url, ig_caption)
                publish_results.append({
                    "platform": "instagram",
                    "success": ig_res.get("success", False),
                    "targetId": ig_res.get("targetId"),
                    "url": ig_res.get("url"),
                    "error": ig_res.get("error")
                })
            except Exception as e:
                publish_results.append({
                    "platform": "instagram",
                    "success": False,
                    "error": str(e)
                })
        else:
            publish_results.append({
                "platform": "instagram",
                "success": False,
                "error": "META_PAGE_ACCESS_TOKEN or INSTAGRAM_ACCOUNT_ID not configured"
            })

    record = {
        "id": broadcast_id,
        "script": script,
        "scenesCount": len(scenes),
        "videoPath": mp4_path,
        "videoPublicUrl": public_video_url,
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
