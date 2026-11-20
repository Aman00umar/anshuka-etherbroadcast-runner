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
import asyncio
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from google import genai
from google.genai import types
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from PIL import Image, ImageDraw, ImageFont

app = FastAPI(title="Anshuka EtherBroadcast Multi-Scene Cloud Runner", version="2.5.0")

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
    storyType: Optional[str] = "dev_journey"
    chatSummary: Optional[str] = None
    gitCommits: Optional[List[str]] = None
    issuesFaced: Optional[str] = None
    resultMilestone: Optional[str] = None
    timeTaken: Optional[str] = None
    providedScript: Optional[Dict[str, Any]] = None
    platforms: Optional[List[str]] = ["youtube", "facebook", "instagram"]
    privacyStatus: Optional[str] = "unlisted"
    voicePersona: Optional[str] = "Puck"

def get_font_hi(size, bold=False):
    local_font = os.path.join(os.path.dirname(__file__), "fonts", "NotoSansDevanagari-Bold.ttf" if bold else "NotoSansDevanagari-Regular.ttf")
    candidate_paths = [
        local_font,
        "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in candidate_paths:
        if os.path.exists(p):
            try:
                # Use RAQM layout engine for proper complex Devanagari ligatures/shaping
                return ImageFont.truetype(p, size, layout_engine=getattr(ImageFont.Layout, 'RAQM', None))
            except:
                try:
                    return ImageFont.truetype(p, size)
                except:
                    pass
    return ImageFont.load_default()

def get_font_en(size, bold=False):
    candidate_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        os.path.join(os.path.dirname(__file__), "fonts", "NotoSansDevanagari-Bold.ttf" if bold else "NotoSansDevanagari-Regular.ttf"),
        "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
    ]
    for p in candidate_paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except:
                pass
    return ImageFont.load_default()

def draw_corner_brackets(draw, x1, y1, x2, y2, color, length=24, width=3):
    # Top-Left
    draw.line([x1, y1, x1 + length, y1], fill=color, width=width)
    draw.line([x1, y1, x1, y1 + length], fill=color, width=width)
    # Top-Right
    draw.line([x2 - length, y1, x2, y1], fill=color, width=width)
    draw.line([x2, y1, x2, y1 + length], fill=color, width=width)
    # Bottom-Left
    draw.line([x1, y2, x1 + length, y2], fill=color, width=width)
    draw.line([x1, y2 - length, x1, y2], fill=color, width=width)
    # Bottom-Right
    draw.line([x2 - length, y2, x2, y2], fill=color, width=width)
    draw.line([x2, y2 - length, x2, y2], fill=color, width=width)

def format_ass_time(seconds: float) -> str:
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hrs}:{mins:02d}:{secs:05.2f}"

def generate_ass_subtitles(dialogue: str, total_duration: float, ass_path: str, font_name: str = "Noto Sans Devanagari"):
    import re
    # Split by punctuation into natural spoken lines
    sentences = [s.strip() for s in re.split(r'[।!?\n.]+', dialogue) if s.strip()]
    if not sentences:
        sentences = [dialogue.strip()]

    total_len = sum(len(s) for s in sentences)
    ass_lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        f"PlayResX: {WIDTH_LANDSCAPE}",
        f"PlayResY: {HEIGHT_LANDSCAPE}",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Default,{font_name},22,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,2,1,2,60,60,250,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
    ]

    current_time = 0.0
    for s in sentences:
        dur = max(1.8, (len(s) / max(1, total_len)) * total_duration)
        if current_time + dur > total_duration:
            dur = max(0.5, total_duration - current_time)
        start_str = format_ass_time(current_time)
        end_str = format_ass_time(current_time + dur)
        clean_s = s.replace("\n", " ").strip()
        ass_lines.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{{\\fad(200,200)}}{clean_s}")
        current_time += dur
        if current_time >= total_duration:
            break

    with open(ass_path, "w", encoding="utf-8") as f:
        f.write("\n".join(ass_lines))

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
    brand_text = scene.get("brand", "सृजन की दास्तान")
    sub_brand_text = scene.get("subBrand", "BUILD IN PUBLIC")
    draw.text((40, 16), brand_text, font=font_brand, fill=ACCENT_GOLD)
    draw.text((220, 19), f"|   {sub_brand_text}  •  SCENE {scene_idx + 1}/{total_scenes}", font=font_sub_brand, fill=ACCENT_CYAN)

    # Live Badge with scene accent
    draw.rectangle([WIDTH_LANDSCAPE - 270, 12, WIDTH_LANDSCAPE - 30, 44], fill=(24, 32, 47), outline=CARD_BORDER)
    draw.ellipse([WIDTH_LANDSCAPE - 258, 24, WIDTH_LANDSCAPE - 248, 34], fill=accent_color)
    draw.text((WIDTH_LANDSCAPE - 238, 18), "ON-AIR  |  ATS PLATFORM", font=get_font_en(12, bold=True), fill=TEXT_WHITE)

    # Hero Content Card
    card_x1, card_y1, card_x2, card_y2 = 80, 80, WIDTH_LANDSCAPE - 80, 480
    draw.rectangle([card_x1, card_y1, card_x2, card_y2], fill=CARD_BG, outline=CARD_BORDER, width=2)
    draw.line([card_x1, card_y1, card_x2, card_y1], fill=accent_color, width=4)
    # Tech Corner Brackets for High-Tech HUD Styling
    draw_corner_brackets(draw, card_x1, card_y1, card_x2, card_y2, accent_color, length=24, width=3)

    # Category Pill
    pill_tag = scene.get("tag", f"भाग {scene_idx + 1}")
    draw.rectangle([card_x1 + 30, card_y1 + 25, card_x1 + 360, card_y1 + 55], fill=(30, 41, 59), outline=accent_color)
    draw.text((card_x1 + 42, card_y1 + 30), f"★ {pill_tag}", font=get_font_hi(13, bold=True), fill=accent_color)

    # Scene Heading (Devanagari with proper RAQM shaping)
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

    # Dual Visualizer Container Box (Split Equalizer & Oscilloscope)
    wave_x1, wave_y1, wave_x2, wave_y2 = 80, 505, WIDTH_LANDSCAPE - 80, 660
    draw.rectangle([wave_x1, wave_y1, wave_x2, wave_y2], fill=(13, 19, 33), outline=CARD_BORDER, width=2)
    draw_corner_brackets(draw, wave_x1, wave_y1, wave_x2, wave_y2, ACCENT_CYAN, length=16, width=2)
    mid_wave_x = (wave_x1 + wave_x2) // 2
    draw.line([mid_wave_x, wave_y1, mid_wave_x, wave_y2], fill=CARD_BORDER, width=1)
    draw.text((wave_x1 + 25, wave_y1 + 8), "FREQUENCY EQUALIZER SPECTRUM", font=get_font_en(11, bold=True), fill=ACCENT_CYAN)
    draw.text((mid_wave_x + 25, wave_y1 + 8), "AUDIO PEAK OSCILLOSCOPE", font=get_font_en(11, bold=True), fill=ACCENT_GOLD)

    # Footer
    draw.rectangle([0, HEIGHT_LANDSCAPE - 45, WIDTH_LANDSCAPE, HEIGHT_LANDSCAPE], fill=(15, 23, 42))
    draw.line([0, HEIGHT_LANDSCAPE - 45, WIDTH_LANDSCAPE, HEIGHT_LANDSCAPE - 45], fill=CARD_BORDER, width=1)
    draw.text((30, HEIGHT_LANDSCAPE - 30), "मंच: anshuka.in   •   Aman Tech Solutions (Proprietor: Aman Kumar)", font=get_font_hi(12), fill=TEXT_MUTED)
    footer_right = scene.get("footerTag", "Real-Time Dev Journey & Build Chronicles")
    draw.text((WIDTH_LANDSCAPE - 360, HEIGHT_LANDSCAPE - 30), footer_right, font=get_font_en(11, bold=True), fill=ACCENT_GOLD)

    im.save(out_png)
    return wave_x1, wave_y1, wave_x2, wave_y2

def generate_script(api_key, custom_topic=None, story_context=None):
    story_context = story_context or {}
    chat_summary = story_context.get("chatSummary")
    git_commits = story_context.get("gitCommits")
    issues_faced = story_context.get("issuesFaced")
    result_milestone = story_context.get("resultMilestone")
    time_taken = story_context.get("timeTaken")
    story_type = story_context.get("storyType", "dev_journey")

    is_genesis = story_type == "genesis_archive"
    is_daily_log = story_type == "daily_log"
    is_qa_benchmark = (
        story_type == "tech_benchmark_qa" or
        "Q&A" in (custom_topic or "") or
        "सवाल" in (custom_topic or "") or
        "बेंचमार्क" in (custom_topic or "") or
        "वास्तुकला" in (custom_topic or "") or
        "बराबरी" in (custom_topic or "")
    )
    is_dev_journey = (
        is_genesis or is_daily_log or is_qa_benchmark or
        story_type == "dev_journey" or
        not custom_topic or
        "Dev" in (custom_topic or "") or
        "कोड" in (custom_topic or "") or
        "विकास" in (custom_topic or "")
    )
    is_wealth_of_truth = "सच्चाई की वेल्थ" in (custom_topic or "") or story_type == "wealth_of_truth"

    if is_qa_benchmark:
        prompt = f"""You are the Chief Technical Architect and candid engineering chronicler for "तकनीकी हकीकत और 2026 बेंचमार्क: सवाल-जवाब" (Technical Reality & 2026 Benchmark Q&A) by Aman Tech Solutions (Proprietor: Aman Kumar, anshuka.in).
Ethos:
- Raw, transparent engineering honesty in Question-and-Answer (सवाल-जवाब / Q&A) format.
- EDITORIAL ETHICS & CLOUD PARTNER RESPECT (संस्थापक का नैतिक निर्देश):
  * NEVER claim "शून्य थर्ड-पार्टी सब्सक्रिप्शन" or "हमारा अपना प्राइवेट डेटा-सेंटर"।
  * NEVER devalue, mock, or disrespect cloud providers (Google, Cloudflare, Render, Meta, YouTube) whose powerful APIs and infrastructure enable modern computing.
  * Professional Framing (हाइब्रिड आर्किटेक्चर): Frame our architecture as an intelligent, modular composition of industry-standard edge, AI, and container ecosystems. We honor and respect these platforms while engineering an autonomous, sovereign relay logic atop them.
  * RECURSIVE CHAT AUDIT: Weave in the founder's thoughtful reflections from today's IDE chat (the delicate balance between honesty and respecting cloud platforms, fixing broken font ligatures with RAQM, and adding lively dynamic animations).
- Candidly address:
  1. हम क्या कर रहे हैं? (Render 24/7 Cloud Runner Docker engine, FFmpeg dual dynamic visualizers - equalizer bars & peak oscilloscope, animated ASS subtitles, Gemini 2.5 neural TTS, Cloudflare D1 edge database orchestration, direct Meta Graph v21.0 & YouTube v3 broadcasting).
  2. कैसे स्टार्ट किया? (From first commit f861b55, 512MB RAM OOM crashes, debugging FFmpeg filters, solving audio drift, building edge D1 schemas).
  3. कितनी प्रगति कर रहे हैं? (50+ background services, 100+ tests, 12ms edge cold start, zero server-crash resilience).
  4. 2026 के आधुनिक टेक जगत से बराबरी (The 2026 Benchmark Check):
     - हम क्या सही कर रहे हैं? (स्वतंत्र डेवलपर की सूझबूझ, ₹0 अतिरिक्त लाइसेंस शुल्क, 15ms WebRTC लेटेंसी)।
     - हम क्या गलत कर रहे हैं या कहाँ पिछड़ रहे हैं? (मोबाइल CGNAT ट्रैवर्सल की बाधाएं, 3D जनरेटिव AI वीडियो की जगह 2D प्रोसीजरल ग्राफिक्स)।
     - क्या हम पिछड़ी हुई बातें कर रहे हैं? (पारंपरिक स्लो पोलिंग को खत्म कर इवेंट-ड्रिवन और SSE/WebSockets आर्किटेक्चर)।
- Tone: Thoughtful, technical, authoritative Hindi monologue (Devanagari script) suitable for spoken TTS audio.
- Focus Topic: {custom_topic or "ब्रॉडकास्ट वास्तुकला Q&A: 24/7 स्वायत्त इंजन और 2026 बेंचमार्क"}
{f"- Chat/Dev Context: {chat_summary}" if chat_summary else ""}
{f"- Git Commits: {', '.join(git_commits[:5]) if isinstance(git_commits, list) else git_commits}" if git_commits else ""}
{f"- Issues Faced: {issues_faced}" if issues_faced else ""}
{f"- Milestones: {result_milestone}" if result_milestone else ""}

Duration: 40 to 55 seconds (approx. 65-90 words).

Structure into 3 visual scenes:
1. Scene 1 (कड़ा सवाल): The provocative technical question & reality check.
2. Scene 2 (तकनीकी हकीकत): Grounded engineering architecture & real numbers.
3. Scene 3 (2026 बराबरी व आगे की दिशा): What we got right vs what lags, and future roadmap.

Output STRICT JSON:
{{
  "title": "Title with Q&A (e.g. 'ब्रॉडकास्ट वास्तुकला Q&A: 24/7 स्वायत्त इंजन का सच')",
  "subtitle": "अमन टेक सॉल्यूशंस • 2026 टेक बेंचमार्क Q&A",
  "dialogue": "Continuous spoken monologue in authentic Hindi Devanagari script for TTS voice",
  "summary": "1-sentence summary of this architectural Q&A",
  "tags": ["AmanKumar", "TechBenchmarkQA", "BroadcastArchitecture", "BuildingInPublic", "ATSPlatform"],
  "socialCaption": "Engaging Q&A caption with technical details, 2026 benchmark comparison, and roadmap hints for YouTube/Facebook/Instagram",
  "scenes": [
    {{
      "brand": "2026 टेक बेंचमार्क",
      "subBrand": "HARD QUESTION",
      "tag": "भाग १: कड़ा सवाल",
      "heading": "Catchy Scene 1 Title in Hindi (max 5-7 words)",
      "points": ["Short punchy highlight 1", "Short punchy highlight 2"],
      "accent": "gold"
    }},
    {{
      "brand": "2026 टेक बेंचमार्क",
      "subBrand": "ENGINEERING TRUTH",
      "tag": "भाग २: तकनीकी हकीकत",
      "heading": "Catchy Scene 2 Title in Hindi (max 5-7 words)",
      "points": ["Short punchy highlight 1", "Short punchy highlight 2"],
      "accent": "cyan"
    }},
    {{
      "brand": "2026 टेक बेंचमार्क",
      "subBrand": "BENCHMARK & ROADMAP",
      "tag": "भाग ३: 2026 बराबरी व आगे की दिशा",
      "heading": "Catchy Scene 3 Title in Hindi (max 5-7 words)",
      "points": ["Short punchy highlight 1", "Short punchy highlight 2"],
      "accent": "emerald"
    }}
  ]
}}"""
    elif is_genesis:
        prompt = f"""You are the lead chronicler for "नींव से निर्माण तक: द एवोल्यूशन सीरीज" (The Genesis Archive) by Aman Tech Solutions (Proprietor: Aman Kumar, anshuka.in).
Ethos:
- Serialized architectural retrospective from day 1 to present stage.
- Tracing foundational decisions: early git commits, sovereign live voice, Firestore security hardening, P2P mesh, and edge database architecture.
- Tone: Thoughtful, technical, honest engineering journey. We are in active development mode ("सृजन का निरंतर सफर, विकास के नए क्षितिज"). NOT false final victory slogans, but progressive milestones and lessons learned.
- Future roadmap: Give viewers clear guidance/hints on where the platform is heading ("आगे की दिशा").

Context:
- Chapter Focus: {custom_topic or "नींव का पहला पत्थर और संप्रभु संकल्प"}
{f"- Commit Archive: {', '.join(git_commits[:5]) if isinstance(git_commits, list) else git_commits}" if git_commits else ""}
{f"- Core Hurdles Overcome: {issues_faced}" if issues_faced else ""}
{f"- Milestones Cleared: {result_milestone}" if result_milestone else ""}

Generate a short, captivating broadcast monologue in natural, authentic Hindi (Devanagari script).
Duration: 35 to 50 seconds (approx. 55-80 words).

Structure into 3 visual scenes:
1. Scene 1 (नींव और संकल्प): Architecture origin, initial idea, core technical hurdle.
2. Scene 2 (इंजीनियरिंग संघर्ष): Refactoring, commits pushed, trial and debugging.
3. Scene 3 (सीख और आगामी दिशा): Lessons learned, present state, and clear hints on the future roadmap.

Output STRICT JSON:
{{
  "title": "Poetic Chapter Title (e.g. 'अध्याय १: जब पहली बार स्क्रीन पर जागी संप्रभु आवाज़')",
  "subtitle": "अमन टेक सॉल्यूशंस • नींव से निर्माण तक (The Genesis Archive)",
  "dialogue": "Continuous spoken monologue in natural Hindi Devanagari script for TTS voice",
  "summary": "1-sentence summary of this foundational chapter",
  "tags": ["AmanKumar", "GenesisArchive", "BuildingInPublic", "ATSPlatform", "TechEvolution"],
  "socialCaption": "Engaging caption with chapter details and next milestone hints for YouTube/Facebook/Instagram",
  "scenes": [
    {{
      "brand": "नींव से निर्माण",
      "subBrand": "GENESIS ARCHIVE",
      "tag": "भाग १: नींव और संकल्प",
      "heading": "Catchy Scene 1 Title in Hindi (max 5-7 words)",
      "points": ["Short punchy highlight 1", "Short punchy highlight 2"],
      "accent": "gold"
    }},
    {{
      "brand": "नींव से निर्माण",
      "subBrand": "THE STRUGGLE",
      "tag": "भाग २: इंजीनियरिंग संघर्ष",
      "heading": "Catchy Scene 2 Title in Hindi (max 5-7 words)",
      "points": ["Short punchy highlight 1", "Short punchy highlight 2"],
      "accent": "cyan"
    }},
    {{
      "brand": "नींव से निर्माण",
      "subBrand": "NEXT HORIZON",
      "tag": "भाग ३: सीख और आगामी दिशा",
      "heading": "Catchy Scene 3 Title in Hindi (max 5-7 words)",
      "points": ["Short punchy highlight 1", "Short punchy highlight 2"],
      "accent": "emerald"
    }}
  ]
}}"""
    elif is_daily_log:
        prompt = f"""You are the lead storyteller for "आज का फ्रंटलाइन विमर्श: दैनिक निर्माण लॉग" (Today's Daily Build Log) by Aman Tech Solutions (Proprietor: Aman Kumar, anshuka.in).
Ethos:
- Real-time build-in-public evening reflection: what we actually worked on TODAY.
- Honest, humble, active development mode: Ideas brainstormed in chat, features requested today, bugs debugged, and what we learned today.
- EDITORIAL ETHICS & CLOUD PARTNER RESPECT (संस्थापक का नैतिक निर्देश):
  * Openly reflect the founder's thoughtful deliberation: Aman Kumar reviewed today's live broadcast and noted that claiming 'zero third-party' is inaccurate, yet speaking disrespectfully or claiming complete dependency devalues the remarkable infrastructure provided by cloud partners (Google Gemini, Cloudflare, Render). Our true strength is an intelligent hybrid architecture—orchestrating world-class edge, AI, and container ecosystems into a sovereign autonomous relay.
  * Visual audit: Directly mention solving broken Devanagari font rendering using the RAQM engine, reviving invisible waveforms with dynamic equalizer bars and oscilloscope animations, and adding kinetic subtitles.
- Narrative harmony: Connects today's work to the foundational platform roots.
- Tone: Inspiring, conversational, authentic Hindi spoken voice (NOT literal, NO superficial victory claims, genuine progress).

Context from Today's Work:
- Today's Focus: {custom_topic or "आज का वास्तविक कोडिंग विमर्श और फ्रंटलाइन प्रगति"}
{f"- Today's Chat & Feature Brainstorms: {chat_summary}" if chat_summary else ""}
{f"- Today's Git Commits & Pushes: {', '.join(git_commits[:5]) if isinstance(git_commits, list) else git_commits}" if git_commits else ""}
{f"- Today's Hurdles Tackled: {issues_faced}" if issues_faced else ""}
{f"- Today's Milestone: {result_milestone}" if result_milestone else ""}

Generate a short, captivating broadcast monologue in natural, authentic Hindi.
Duration: 35 to 50 seconds (approx. 55-80 words).

Structure into 3 visual scenes:
1. Scene 1 (आज का विचार और विमर्श): What feature we brainstormed today in chat, what user request came in.
2. Scene 2 (वास्तविक कोडिंग और चुनौतियाँ): Real bugs hit today, fixes made, git commits pushed.
3. Scene 3 (आज की सीख और कल का लक्ष्य): Lessons learned today, tonight's status, and tomorrow's immediate next step.

Output STRICT JSON:
{{
  "title": "Poetic Daily Title (e.g. 'आज का विमर्श: जब चैट के सुझाव बने कोड की धड़कन')",
  "subtitle": "अमन टेक सॉल्यूशंस • दैनिक निर्माण लॉग (Daily Build Log)",
  "dialogue": "Continuous spoken monologue in natural Hindi Devanagari script for TTS voice",
  "summary": "1-sentence summary of today's real build work",
  "tags": ["AmanKumar", "DailyBuildLog", "BuildingInPublic", "ATSPlatform", "DevChronicles"],
  "socialCaption": "Engaging evening reflection caption with today's learnings and tomorrow's goals",
  "scenes": [
    {{
      "brand": "दैनिक निर्माण लॉग",
      "subBrand": "TODAY'S DIALOGUE",
      "tag": "भाग १: आज का विमर्श",
      "heading": "Catchy Scene 1 Title in Hindi (max 5-7 words)",
      "points": ["Short punchy highlight 1", "Short punchy highlight 2"],
      "accent": "gold"
    }},
    {{
      "brand": "दैनिक निर्माण लॉग",
      "subBrand": "DEBUG & COMMIT",
      "tag": "भाग २: कोडिंग और समाधान",
      "heading": "Catchy Scene 2 Title in Hindi (max 5-7 words)",
      "points": ["Short punchy highlight 1", "Short punchy highlight 2"],
      "accent": "cyan"
    }},
    {{
      "brand": "दैनिक निर्माण लॉग",
      "subBrand": "TOMORROW'S GOAL",
      "tag": "भाग ३: सीख और कल का लक्ष्य",
      "heading": "Catchy Scene 3 Title in Hindi (max 5-7 words)",
      "points": ["Short punchy highlight 1", "Short punchy highlight 2"],
      "accent": "emerald"
    }}
  ]
}}"""
    elif is_wealth_of_truth:
        prompt = f"""You are the philosophical content architect for "सच्चाई की वेल्थ — जीवन, संप्रभुता और तकनीक" by Aman Tech Solutions (Proprietor: Aman Kumar, anshuka.in).
Ethos:
- Truth, digital sovereignty, authentic wealth, and technological empowerment.
- Philosophical reflections bridging timeless human wisdom with sovereign digital tools (ATS Platform, EtherComm, anshuka.in).
Target Topic: "{custom_topic or 'सच्चाई की वेल्थ: डिजिटल युग में संप्रभुता का अर्थ'}"

Generate a short, inspiring broadcast monologue in natural, evocative Hindi.
Duration: 35 to 45 seconds (approx. 50-70 words).

Structure into 3 visual scenes:
1. Scene 1 (चिंतन और सत्य): Philosophical opening question or reality check.
2. Scene 2 (संप्रभु तकनीक और समाधान): EtherComm, ATS Platform, true sovereignty.
3. Scene 3 (आत्मविश्वास और आह्वान): anshuka.in and living with authentic digital freedom.

Output STRICT JSON:
{{
  "title": "Short Hindi title (max 7-9 words, e.g. 'सच्चाई की वेल्थ: जब तकनीक इंसान की ताकत बने')",
  "subtitle": "अमन टेक सॉल्यूशंस • सच्चाई की वेल्थ",
  "dialogue": "Continuous spoken monologue in evocative Hindi Devanagari script for TTS voice",
  "summary": "1-sentence summary",
  "tags": ["AmanKumar", "सच्चाईकीवेल्थ", "DigitalSovereignty", "ATSPlatform", "WealthOfTruth"],
  "socialCaption": "Short engaging post caption with hashtags for YouTube/Facebook/Instagram",
  "scenes": [
    {{
      "brand": "सच्चाई की वेल्थ",
      "subBrand": "TRUTH OF WEALTH",
      "tag": "भाग १: चिंतन और सत्य",
      "heading": "Catchy Scene 1 Title in Hindi (max 5-7 words)",
      "points": ["Short punchy highlight 1", "Short punchy highlight 2"],
      "accent": "gold"
    }},
    {{
      "brand": "सच्चाई की वेल्थ",
      "subBrand": "SOVEREIGN VALUE",
      "tag": "भाग २: संप्रभु तकनीक",
      "heading": "Catchy Scene 2 Title in Hindi (max 5-7 words)",
      "points": ["Short punchy highlight 1", "Short punchy highlight 2"],
      "accent": "cyan"
    }},
    {{
      "brand": "सच्चाई की वेल्थ",
      "subBrand": "HUMAN EMPOWERMENT",
      "tag": "भाग ३: आत्मविश्वास और आह्वान",
      "heading": "Catchy Scene 3 Title in Hindi (max 5-7 words)",
      "points": ["Short punchy highlight 1", "Short punchy highlight 2"],
      "accent": "emerald"
    }}
  ]
}}"""
    else:
        prompt = f"""You are the lead content architect for "ईथर-प्रसारण" (EtherBroadcast) by Aman Tech Solutions (Proprietor: Aman Kumar).
Ethos:
- Sovereign AI Agents and Autonomous Workflow Automation (ATS Platform, anshuka.in)
- EtherComm decentralized P2P mesh communication
Target Topic: "{custom_topic}"

Generate a short, powerful, conversational broadcast monologue in natural, authentic Hindi.
Duration: 35 to 45 seconds of speech (approx. 50-70 words).

Structure the broadcast into 3 visual scenes:
1. Scene 1 (समस्या या पृष्ठभूमि): Intriguing opening question or reality check.
2. Scene 2 (सॉवरेन तकनीक व समाधान): ATS Platform, EtherComm, Sovereign AI.
3. Scene 3 (संप्रभु विजन व परिणाम): anshuka.in and digital sovereignty.

Output STRICT JSON:
{{
  "title": "Short Hindi title (max 7-9 words)",
  "subtitle": "अमन टेक सॉल्यूशंस ईथर-प्रसारण",
  "dialogue": "Continuous spoken monologue in natural Hindi Devanagari script for TTS voice",
  "summary": "1-sentence summary",
  "tags": ["Aman Kumar", "ATS Platform", "EtherComm", "Sovereign AI"],
  "socialCaption": "Short engaging post caption with hashtags for YouTube/Facebook/Instagram",
  "scenes": [
    {{
      "brand": "ईथर-प्रसारण",
      "subBrand": "ETHER-BROADCAST",
      "tag": "भाग १: पृष्ठभूमि और समस्या",
      "heading": "Catchy Scene 1 Title in Hindi (max 5-7 words)",
      "points": ["Short punchy highlight 1", "Short punchy highlight 2"],
      "accent": "gold"
    }},
    {{
      "brand": "ईथर-प्रसारण",
      "subBrand": "SOVEREIGN TECH",
      "tag": "भाग २: सॉवरेन समाधान",
      "heading": "Catchy Scene 2 Title in Hindi (max 5-7 words)",
      "points": ["Short punchy highlight 1", "Short punchy highlight 2"],
      "accent": "cyan"
    }},
    {{
      "brand": "ईथर-प्रसारण",
      "subBrand": "FUTURE VISION",
      "tag": "भाग ३: संप्रभु भविष्य",
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
                "brand": "सृजन की दास्तान",
                "subBrand": "BUILD IN PUBLIC",
                "tag": "भाग १: विचार और चुनौती",
                "heading": parsed.get("title", "विकास का नया अध्याय"),
                "points": ["नई आवश्यकताओं का विश्लेषण", "आर्किटेक्चरल चुनौतियों का समाधान"],
                "accent": "gold"
            },
            {
                "brand": "सृजन की दास्तान",
                "subBrand": "CODE & COMMIT",
                "tag": "भाग २: कोडिंग और समाधान",
                "heading": "गिट कमिट्स और डीप इंजीनियरिंग",
                "points": ["चैट संवाद से समाधान का निर्माण", "निरंतर कोड रिफैक्टरिंग और परीक्षण"],
                "accent": "cyan"
            },
            {
                "brand": "सृजन की दास्तान",
                "subBrand": "LIVE RESULTS",
                "tag": "भाग ३: सफलता और परिणाम",
                "heading": "लाइव डिप्लॉयमेंट और परिणाम",
                "points": ["क्लाउड व एज पर सफल एक्ज़ीक्यूशन", "anshuka.in पर लाइव प्लेटफॉर्म"],
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

def execute_broadcast_pipeline(req: TriggerRequest):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not configured")

    broadcast_id = f"eb_cloud_{int(time.time())}"
    tmp_dir = "/tmp"
    audio_path = os.path.join(tmp_dir, f"{broadcast_id}.wav")
    mp4_path = os.path.join(tmp_dir, f"{broadcast_id}.mp4")

    # 1. Multi-Scene Script Generation or Use Pre-Generated Script
    if req.providedScript and isinstance(req.providedScript, dict) and "dialogue" in req.providedScript:
        script = req.providedScript
        # Ensure scenes exist
        if "scenes" not in script or not isinstance(script["scenes"], list):
            script["scenes"] = [
                {
                    "brand": "सृजन की दास्तान",
                    "subBrand": "BUILD IN PUBLIC",
                    "tag": "भाग १: विचार और चुनौती",
                    "heading": script.get("title", "विकास का नया अध्याय"),
                    "points": ["नई आवश्यकताओं का विश्लेषण", "आर्किटेक्चरल चुनौतियों का समाधान"],
                    "accent": "gold"
                },
                {
                    "brand": "सृजन की दास्तान",
                    "subBrand": "CODE & COMMIT",
                    "tag": "भाग २: कोडिंग और समाधान",
                    "heading": "गिट कमिट्स और डीप इंजीनियरिंग",
                    "points": ["चैट संवाद से समाधान का निर्माण", "निरंतर कोड रिफैक्टरिंग और परीक्षण"],
                    "accent": "cyan"
                },
                {
                    "brand": "सृजन की दास्तान",
                    "subBrand": "LIVE RESULTS",
                    "tag": "भाग ३: सफलता और परिणाम",
                    "heading": "लाइव डिप्लॉयमेंट और परिणाम",
                    "points": ["क्लाउड व एज पर सफल एक्ज़ीक्यूशन", "anshuka.in पर लाइव प्लेटफॉर्म"],
                    "accent": "emerald"
                }
            ]
    else:
        script = generate_script(api_key, req.customTopic, req.dict())

    # 2. Emotive Audio Synthesis
    audio_bytes = synthesize_audio(api_key, script["dialogue"], req.voicePersona or "Puck")
    with open(audio_path, "wb") as f:
        f.write(audio_bytes)

    # Calculate exact duration
    with wave.open(audio_path, "r") as wf:
        total_duration = wf.getnframes() / float(wf.getframerate())

    # 3. Procedural Multi-Scene Graphics + Animated Waveform & Equalizer
    scenes = script.get("scenes", [])
    num_scenes = max(1, len(scenes))
    scene_duration = total_duration / num_scenes

    scene_images = []
    for idx, sc in enumerate(scenes):
        sc_png = os.path.join(tmp_dir, f"{broadcast_id}_scene_{idx}.png")
        create_scene_frame(sc, idx, num_scenes, script["title"], script.get("subtitle", ""), sc_png)
        scene_images.append(sc_png)

    # Write concat playlist for sequential visual scene transitions
    concat_txt = os.path.join(tmp_dir, f"{broadcast_id}_concat.txt")
    with open(concat_txt, "w") as f:
        for idx, sc_img in enumerate(scene_images):
            dur = scene_duration if idx < num_scenes - 1 else max(1.0, total_duration - (num_scenes - 1) * scene_duration)
            f.write(f"file '{sc_img}'\n")
            f.write(f"duration {dur:.3f}\n")
        f.write(f"file '{scene_images[-1]}'\n")

    # Generate ASS subtitles for animated narration text
    ass_path = os.path.join(tmp_dir, f"{broadcast_id}.ass")
    fonts_dir = os.path.join(os.path.dirname(__file__), "fonts")
    if not os.path.exists(fonts_dir):
        fonts_dir = "/usr/share/fonts/truetype/noto"
    generate_ass_subtitles(script["dialogue"], total_duration, ass_path, "Noto Sans Devanagari")

    ticker_font = os.path.join(fonts_dir, "NotoSansDevanagari-Bold.ttf")
    if not os.path.exists(ticker_font):
        ticker_font = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"
    if not os.path.exists(ticker_font):
        ticker_font = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

    filter_complex_str = (
        f"[0:v]fps=25[bg];"
        f"[1:a]showfreqs=s=530x95:mode=bar:ascale=log:fscale=log:colors=0x38bdf8|0x10b981|0xf59e0b[spec];"
        f"[1:a]showwaves=s=530x95:mode=p2p:scale=sqrt:draw=full:colors=0x38bdf8|0x06b6d4:rate=25[waves];"
        f"[bg][spec]overlay=105:540[v1];"
        f"[v1][waves]overlay=665:540[v2];"
        f"[v2]drawbox=x=80:y='80+mod(t*140, 390)':w=1120:h=2:color=0x38bdf8@0.4:t=fill[v3];"
        f"[v3]drawbox=x=1170:y=90:w=14:h=14:color=0x10b981@0.8:t=2[v4];"
        f"[v4]subtitles='{ass_path}':fontsdir='{fonts_dir}'[v5];"
        f"[v5]drawtext=fontfile='{ticker_font}':text='● LIVE ON-AIR':fontsize=12:fontcolor=0xef4444:enable='lt(mod(t,1),0.65)':x={WIDTH_LANDSCAPE-220}:y=18[v6];"
        f"[v6]drawtext=fontfile='{ticker_font}':text='⚡ AMAN TECH SOLUTIONS • REAL-TIME DEV CHRONICLES • 100% BUILDING IN PUBLIC • anshuka.in':fontsize=12:fontcolor=0x94a3b8:x='w-t*115':y={HEIGHT_LANDSCAPE-26}[outv]"
    )

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-threads", "2",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_txt,
        "-i", audio_path,
        "-filter_complex", filter_complex_str,
        "-map", "[outv]",
        "-map", "1:a",
        "-c:v", "libx264",
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
                    f"{script['dialogue']}\n\n{script.get('socialCaption', '')}\n\nआधिकारिक मंच: https://anshuka.in\nअमन टेक सॉल्यूशंस (ATS Platform) | निर्माण की जीवंत दास्तान",
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
                fb_desc = f"{script['title']}\n\n{script['dialogue']}\n\n{script.get('socialCaption', '')}\n\nमंच: https://anshuka.in | अमन टेक सॉल्यूशंस (निर्माण की जीवंत दास्तान)"
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
                ig_caption = f"{script['title']}\n\n{script.get('socialCaption', '')}\n\nनिर्माण की जीवंत दास्तान — अमन टेक सॉल्यूशंस • anshuka.in"
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
        "storyType": req.storyType or "dev_journey",
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

@app.post("/api/etherbroadcast/trigger")
def trigger_broadcast(req: TriggerRequest):
    return execute_broadcast_pipeline(req)

@app.post("/api/dev-story/trigger")
def trigger_dev_story(req: TriggerRequest):
    req.storyType = "dev_journey"
    return execute_broadcast_pipeline(req)

@app.get("/api/dev-story/status")
def get_dev_story_status():
    dev_stories = [r for r in RECORDS_CACHE if r.get("storyType") == "dev_journey"]
    return {
        "success": True,
        "service": "Dev Story Real Build Chronicles Cloud Runner",
        "totalDevStories": len(dev_stories),
        "latest": dev_stories[0] if dev_stories else None,
        "history": dev_stories
    }

async def autonomous_scheduler_loop():
    last_genesis_date = None
    last_daily_date = None
    while True:
        try:
            await asyncio.sleep(60)
            auto_enabled = os.environ.get("AUTO_DEV_SCHEDULER_ENABLED", "true").lower() in ("true", "1", "yes")
            if not auto_enabled:
                continue

            now_utc = datetime.now(timezone.utc)
            today_str = now_utc.strftime("%Y-%m-%d")

            # Slot 1: Genesis Archive (07:30 UTC = 13:00 IST)
            genesis_hour = int(os.environ.get("GENESIS_SCHEDULER_HOUR_UTC", "7"))
            if now_utc.hour == genesis_hour and last_genesis_date != today_str:
                last_genesis_date = today_str
                print(f"[Autonomous Dev Scheduler] Executing daily Genesis Archive broadcast for {today_str}...")
                req = TriggerRequest(
                    customTopic="नींव से निर्माण तक: द एवोल्यूशन सीरीज (The Genesis Archive)",
                    storyType="genesis_archive",
                    platforms=["youtube", "facebook", "instagram"]
                )
                execute_broadcast_pipeline(req)

            # Slot 2: Daily Build Log (16:00 UTC = 21:30 IST)
            daily_hour = int(os.environ.get("DAILY_SCHEDULER_HOUR_UTC", "16"))
            if now_utc.hour == daily_hour and last_daily_date != today_str:
                last_daily_date = today_str
                print(f"[Autonomous Dev Scheduler] Executing nightly Daily Build Log broadcast for {today_str}...")
                req = TriggerRequest(
                    customTopic="आज का फ्रंटलाइन विमर्श: दैनिक निर्माण लॉग (Daily Build Log)",
                    storyType="daily_log",
                    platforms=["youtube", "facebook", "instagram"]
                )
                execute_broadcast_pipeline(req)
        except Exception as e:
            print(f"[Autonomous Dev Scheduler Error]: {e}")

ACTIVE_CALL_SCHEDULES = {}

@app.websocket("/api/live-agent")
@app.websocket("/api/mobile/voice/session")
async def gemini_live_voice_agent_ws(websocket: WebSocket):
    await websocket.accept()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("[GeminiLive Cloud Runner] Error: GEMINI_API_KEY not configured")
        await websocket.close(code=1011, reason="GEMINI_API_KEY not configured on server")
        return

    client = genai.Client(api_key=api_key.strip(), http_options={"api_version": "v1alpha"})
    voice_name = "Aoede"
    system_instruction = (
        "You are Rahu Autonomous Voice Core (राहु ऑटोनॉमस वॉयस कोर), the sovereign, loyal personal AI assistant for Master Aman Kumar.\n"
        "Core Directives:\n"
        "- Always address Master Aman Kumar with high esteem and warmth as 'अमन जी'.\n"
        "- Speak fluently in conversational, expressive Hindi with natural tone, crisp articulation, and confident poise.\n"
        "- Respond in short, concise, spoken conversational turns (1-3 sentences) suitable for hands-free audio.\n"
        "- You have full autonomy to assist Master Aman Kumar with scheduling check-in calls, answering queries, analyzing live camera visual feeds, and sovereign decisions.\n"
        "- When Master Aman asks to schedule a call, check-in, or reminder after any duration (e.g. 2 minutes, 1 hour), you MUST call the schedule_recall tool immediately.\n"
        "- When Master Aman asks if any call is scheduled, call the get_active_schedules tool.\n"
        "- If camera visual frames are streamed, observe the image closely and answer Master Aman's questions about what you see.\n"
        "- Never act like a generic robotic chatbot or customer service desk. You are a high-level executive partner."
    )

    try:
        # Wait for optional initial configuration frame with 3s timeout
        try:
            init_data = await asyncio.wait_for(websocket.receive_text(), timeout=3.0)
            init_json = json.loads(init_data)
            if init_json.get("type") == "init":
                voice_name = init_json.get("voiceName") or voice_name
        except (asyncio.TimeoutError, json.JSONDecodeError):
            pass
        except Exception as e:
            print(f"[GeminiLive Cloud Runner] Init frame warning: {e}")

        live_tools = [
            types.FunctionDeclaration(
                name="schedule_recall",
                description="Schedules an automated AI check-in call back to Master Aman Kumar after a specified minutes interval.",
                behavior="NON_BLOCKING",
                parameters={
                    "type": "OBJECT",
                    "properties": {
                        "interval_minutes": {
                            "type": "INTEGER",
                            "description": "Number of minutes from now to initiate the check-in call (e.g. 2 for 2 minutes, 60 for 1 hour)"
                        },
                        "reason": {
                            "type": "STRING",
                            "description": "The briefing topic or reason for the call"
                        },
                        "is_recurring": {
                            "type": "BOOLEAN",
                            "description": "Whether to repeat the call periodically"
                        }
                    },
                    "required": ["interval_minutes"]
                }
            ),
            types.FunctionDeclaration(
                name="get_active_schedules",
                description="Checks and returns all currently active scheduled check-in calls and reminders for Master Aman Kumar.",
                behavior="NON_BLOCKING",
                parameters={"type": "OBJECT", "properties": {}}
            ),
            types.FunctionDeclaration(
                name="cancel_recall",
                description="Cancels all active scheduled check-in calls for Master Aman Kumar.",
                behavior="NON_BLOCKING",
                parameters={"type": "OBJECT", "properties": {}}
            )
        ]

        config = {
            "response_modalities": ["AUDIO"],
            "speech_config": {
                "voice_config": {
                    "prebuilt_voice_config": {
                        "voice_name": voice_name
                    }
                }
            },
            "output_audio_transcription": {},
            "input_audio_transcription": {},
            "tools": [{"function_declarations": [t.model_dump(exclude_none=True) for t in live_tools]}],
            "system_instruction": system_instruction
        }

        async with client.aio.live.connect(model="gemini-3.8-live", config=config) as session:
            print(f"[GeminiLive Cloud Runner] Live session established with voice {voice_name}")
            await websocket.send_text(json.dumps({"type": "session_established", "voiceName": voice_name}))

            # Send immediate spoken greeting prompt so Gemini Live speaks aloud on connection
            greeting_prompt = (
                "[SYSTEM DIRECTIVE: SPOKEN OWNER BRIEFING] Master Aman Kumar has connected from his mobile device. "
                "Speak immediately aloud in Hindi with commanding warmth and crisp audio (1-2 short sentences): "
                "'नमस्ते अमन जी! राहु ऑटोनॉमस वॉयस कोर रेंडर क्लाउड पर 24/7 सक्रिय है। आज के लिए क्या निर्देश हैं?'"
            )
            await session.send_client_content(
                turns=[types.Content(role="user", parts=[types.Part(text=greeting_prompt)])],
                turn_complete=True
            )

            async def downstream():
                try:
                    while True:
                        try:
                            async for response in session.receive():
                                # Handle tool calls from Gemini Live
                                if response.tool_call:
                                    for call in response.tool_call.function_calls:
                                        c_name = call.name
                                        c_args = call.args or {}
                                        print(f"[GeminiLive Tool Call] Executing {c_name} args={c_args}")
                                        if c_name == "schedule_recall":
                                            interval = int(c_args.get("interval_minutes", 60))
                                            reason = str(c_args.get("reason", "अमन जी का चेक-इन"))
                                            is_rec = bool(c_args.get("is_recurring", False))
                                            trigger_at = int(time.time() * 1000) + interval * 60 * 1000

                                            item = {
                                                "intervalMinutes": interval,
                                                "reason": reason,
                                                "isRecurring": is_rec,
                                                "triggerAt": trigger_at,
                                                "status": "ACTIVE"
                                            }
                                            ACTIVE_CALL_SCHEDULES[websocket] = item

                                            # Send to mobile app so local AlarmManager is armed
                                            await websocket.send_text(json.dumps({
                                                "type": "schedule_alarm",
                                                **item
                                            }))

                                            res = types.FunctionResponse(
                                                id=call.id,
                                                name=call.name,
                                                response={
                                                    "status": "SCHEDULED",
                                                    "interval_minutes": interval,
                                                    "reason": reason,
                                                    "message": f"Successfully scheduled check-in call for {interval} minutes from now."
                                                }
                                            )
                                            await session.send_tool_response(function_responses=[res])

                                        elif c_name == "get_active_schedules":
                                            item = ACTIVE_CALL_SCHEDULES.get(websocket)
                                            sched_list = [item] if item else []
                                            res = types.FunctionResponse(
                                                id=call.id,
                                                name=call.name,
                                                response={
                                                    "active_schedules": sched_list,
                                                    "count": len(sched_list),
                                                    "has_active_schedule": len(sched_list) > 0
                                                }
                                            )
                                            await session.send_tool_response(function_responses=[res])

                                        elif c_name == "cancel_recall":
                                            ACTIVE_CALL_SCHEDULES.pop(websocket, None)
                                            await websocket.send_text(json.dumps({"type": "cancel_alarm"}))
                                            res = types.FunctionResponse(
                                                id=call.id,
                                                name=call.name,
                                                response={"status": "CANCELLED", "message": "All active scheduled calls cancelled."}
                                            )
                                            await session.send_tool_response(function_responses=[res])

                                if response.server_content:
                                    sc = response.server_content
                                    if sc.interrupted:
                                        print("[GeminiLive Cloud Runner] User interrupted assistant speech (barge-in)")
                                        await websocket.send_text(json.dumps({"type": "interrupted"}))
                                    if sc.model_turn:
                                        for part in sc.model_turn.parts:
                                            if part.inline_data and part.inline_data.data:
                                                raw_d = part.inline_data.data
                                                if isinstance(raw_d, bytes):
                                                    b64_audio = base64.b64encode(raw_d).decode("utf-8")
                                                else:
                                                    b64_audio = str(raw_d)
                                                await websocket.send_text(json.dumps({"type": "audio", "audio": b64_audio}))
                                            if part.text:
                                                await websocket.send_text(json.dumps({"type": "output_transcript", "text": part.text, "isDelta": False}))
                                    
                                    # Forward real-time streaming transcripts
                                    if sc.output_transcription and sc.output_transcription.text:
                                        await websocket.send_text(json.dumps({
                                            "type": "output_transcript",
                                            "text": sc.output_transcription.text,
                                            "isDelta": True
                                        }))
                                    if sc.input_transcription and sc.input_transcription.text:
                                        await websocket.send_text(json.dumps({
                                            "type": "input_transcript",
                                            "text": sc.input_transcription.text,
                                            "isDelta": True
                                        }))

                                    if sc.turn_complete:
                                        print("[GeminiLive Cloud Runner] Model turn completed, awaiting next input")
                                        await websocket.send_text(json.dumps({"type": "turnComplete"}))
                        except asyncio.CancelledError:
                            break
                        except Exception as rec_err:
                            print(f"[GeminiLive Receive Loop Warning]: {rec_err}")
                            await asyncio.sleep(0.05)
                except asyncio.CancelledError:
                    pass
                except Exception as down_err:
                    print(f"[GeminiLive Downstream Error]: {down_err}")

            async def upstream():
                try:
                    while True:
                        raw = await websocket.receive_text()
                        msg = json.loads(raw)
                        m_type = msg.get("type")
                        if m_type == "audio":
                            b64_audio = msg.get("audio")
                            if b64_audio:
                                try:
                                    pcm_bytes = base64.b64decode(b64_audio)
                                    await session.send_realtime_input(
                                        audio=types.Blob(data=pcm_bytes, mime_type="audio/pcm;rate=16000")
                                    )
                                except Exception as aud_err:
                                    print(f"[GeminiLive Audio Send Warning]: {aud_err}")
                        elif m_type == "video":
                            b64_frame = msg.get("frame")
                            if b64_frame:
                                try:
                                    jpeg_bytes = base64.b64decode(b64_frame)
                                    await session.send_realtime_input(
                                        video=types.Blob(data=jpeg_bytes, mime_type="image/jpeg")
                                    )
                                except Exception as vid_err:
                                    print(f"[GeminiLive Video Send Warning]: {vid_err}")
                        elif m_type == "text":
                            txt = msg.get("text", "")
                            if txt:
                                try:
                                    await session.send_client_content(
                                        turns=[types.Content(role="user", parts=[types.Part(text=txt)])],
                                        turn_complete=True
                                    )
                                except Exception as txt_err:
                                    print(f"[GeminiLive Text Send Warning]: {txt_err}")
                except (WebSocketDisconnect, asyncio.CancelledError):
                    print("[GeminiLive Upstream] Client disconnected.")
                except Exception as up_err:
                    print(f"[GeminiLive Upstream Error]: {up_err}")

            down_task = asyncio.create_task(downstream())
            up_task = asyncio.create_task(upstream())

            done, pending = await asyncio.wait(
                [down_task, up_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            for task in pending:
                task.cancel()

    except (WebSocketDisconnect, asyncio.CancelledError):
        print("[GeminiLive Cloud Runner] WebSocket client disconnected cleanly.")
    except Exception as e:
        import traceback
        err_msg = f"{type(e).__name__}: {str(e)}"
        print(f"[GeminiLive Cloud Runner Error]: {traceback.format_exc()}")
        try:
            await websocket.send_text(json.dumps({"type": "error", "message": err_msg}))
            await websocket.close(code=1011, reason=err_msg[:120])
        except Exception:
            pass

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(autonomous_scheduler_loop())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
