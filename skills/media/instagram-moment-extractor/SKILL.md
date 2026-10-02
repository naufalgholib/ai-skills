---
name: instagram-moment-extractor
description: Extract high-definition portfolio moments and video frames from Instagram Reels, Stories, Highlights, and Posts with 3-tier fallback access (public yt-dlp, active browser session, cookie injection), precise FFmpeg micro-sampling, and dual-format PNG lossless + WebP web optimization.
---

# Instagram Moment Extractor

Extract high-definition visual assets and portfolio moments from Instagram media (Reels, Feed Posts, Stories, Highlights) with frame-accurate FFmpeg sampling and dual-format output.

## Core Capabilities

1. **Intelligent URL Detection & Routing**:
   - Reels (`/reel/<code>`)
   - Standard Feed Posts (`/p/<code>`)
   - Story Highlights (`/s/<encoded_highlight>` or `highlight:<id>`)
   - Stories (`/stories/<username>/<story_id>`)

2. **3-Tier Fallback Media Access Strategy**:
   - **Tingkat 1 (Public Access / Tanpa Login)**: Direct extraction using standalone `yt-dlp` with format selection (`-f "bv*+ba/b"`). Works for public Reels and feed videos without credentials.
   - **Tingkat 2 (Active Browser Session / Orca ADE)**: For media behind login walls (e.g. Stories, private profiles, highlight archives), inspect the active authenticated session in the user's browser (Orca ADE / Chromium tab) to capture DOM network stream URLs or download directly.
   - **Tingkat 3 (Session Cookie Injection)**: Inject Instagram session cookies (`sessionid`, `ds_user_id`) into headless scrapers or `yt-dlp --cookies` to bypass authentication barriers programmatically.

3. **FFmpeg Micro-Sampling for Crisp, Blur-Free Frames**:
   - Seek accuracy with input seeking (`-ss <timestamp> -i <video> -frames:v 1`).
   - Frame micro-stepping (+/- 100ms) to avoid intermediate motion blur during fast action.
   - Native resolution preservation (e.g. 720x1280 vertical video).

4. **Dual-Format Output Architecture**:
   - **PNG Master**: Lossless reference frame for archival and high-fidelity inspection.
   - **WebP Web-Optimized**: Modern web standard (`-c:v libwebp -q:v 85`), achieving 85–90% file size reduction while preserving visual crispness.

---

## Architecture & Workflow

```
[Instagram URL / Local Video]
           │
           ▼
[URL Type Classifier]
  ├── Reel / Post (Public) ───────► Tingkat 1: yt-dlp direct download
  └── Story / Highlight (Auth) ───► Tingkat 2: Active Browser session
                                └─► Tingkat 3: Cookie injection (--cookies)
           │
           ▼
    [Master Video File]
           │
           ▼
[FFmpeg Micro-Sampling Engine]
  Seek: -ss HH:MM:SS.mmm -frames:v 1
           │
           ├──────────────────────────────┐
           ▼                              ▼
 [PNG Lossless Master]        [WebP Web-Optimized]
  (720x1280 Native)           (-c:v libwebp -q:v 85)
           │                              │
           └──────────────┬───────────────┘
                          ▼
            [Portfolio Manifest JSON]
```

---

## Usage Guide

### CLI Automation Tool

The skill bundles a standalone CLI script located at:
`scripts/extract_moments.py`

#### 1. Extract from Public Reel (Tanpa Login)
```bash
python3 scripts/extract_moments.py \
  --url "https://www.instagram.com/reel/<shortcode>/" \
  --timestamps "00:00:09.600" "00:00:16.600" "00:00:19.400" \
  --names "moment_01_speech" "moment_02_entrance" "moment_03_stage" \
  --output-dir "./portfolio/sample-project" \
  --webp-quality 85
```

#### 2. Extract from Local Video File
```bash
python3 scripts/extract_moments.py \
  --video "/path/to/video.mp4" \
  --timestamps "00:00:08.500" "00:00:18.000" \
  --names "moment_01_ceremony" "moment_02_celebration" \
  --output-dir "./portfolio/ceremony"
```

#### 3. Extract with Cookie Authentication (Tingkat 3 Fallback)
```bash
python3 scripts/extract_moments.py \
  --url "https://www.instagram.com/s/<encoded_highlight_url>" \
  --cookies "/path/to/cookies.txt" \
  --timestamps "00:00:05.000" \
  --names "highlight_moment_01" \
  --output-dir "./portfolio/highlight"
```

---

## Direct FFmpeg Recipes

When running commands manually:

### 1. Extract Lossless PNG Frame
```bash
ffmpeg -y -ss 00:00:09.600 -i input.mp4 -frames:v 1 output.png
```

### 2. Convert PNG to Web-Optimized WebP
```bash
ffmpeg -y -i output.png -c:v libwebp -q:v 85 output.webp
```

### 3. Verify Resolution & Frame Info
```bash
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,duration -of csv=s=x:p=0 output.png
```

---

## Troubleshooting & Best Practices

1. **Authentication Error on Stories/Highlights**:
   Instagram Stories and Highlights require session tokens. When anonymous access fails:
   - Check if the same event or video was posted as a public Reel or feed post on the creator's profile.
   - If not, provide session cookies via `--cookies` or attach an active authenticated browser session.

2. **Avoiding Motion Blur (Micro-Sampling)**:
   Fast-action video frequently features hand-held camera movement. If a chosen timestamp lands on a blurred transition frame, adjust the timestamp by `+0.100s` or `-0.100s` to capture the still apex of the motion.

3. **Manifest Compilation**:
   Always maintain a structured manifest indexing asset metadata, original Instagram source links, relative paths for both PNG and WebP formats, timestamps, and semantic descriptions for landing page integration.
