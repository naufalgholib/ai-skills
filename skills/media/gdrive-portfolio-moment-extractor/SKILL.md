---
name: gdrive-portfolio-moment-extractor
description: Extract high-definition portfolio moments and video frames directly from Google Drive raw & edited footage (Full HD/4K) without API keys or authentication, featuring zero-auth virus scan bypass, FFmpeg micro-sampling with edge-variance sharpness selection, dual-format lossless PNG + WebP web optimization, and structured portfolio manifest generation.
---

# Google Drive Portfolio Moment Extractor

Extract master high-definition visual assets (Full HD 1080p, 4K, high-res photos) directly from Google Drive video and image footage without requiring Google Cloud API credentials or login.

## Core Capabilities

1. **Zero-Auth Direct Google Drive Stream Access**:
   - **Video Endpoint**: Downloads raw video files via `https://drive.usercontent.google.com/download?id={file_id}&export=download&authuser=0`.
   - **Virus Scan Warning Bypass**: Automatically parses Google's intermediate warning page for large files (>100MB), extracts security form tokens (`uuid`, `confirm=t`), and captures the binary stream using persistent session cookies (`http.cookiejar.CookieJar`).
   - **High-Res Photo Extraction**: Exploits Google Drive's high-resolution render endpoint `https://drive.google.com/thumbnail?id={file_id}&sz=w4000`, fetching full uncompressed renders (up to 4000x5333) for HEIC and high-res JPG formats without local HEIC decoder dependencies.

2. **FFmpeg Micro-Sampling for Blur-Free Frames**:
   - Eliminates video motion blur, transition crossfades, and blinking eyes by evaluating a micro-sampling window (e.g. $\pm 0.4$s, 5 steps) around candidate timestamps.
   - Evaluates frame sharpness via edge filter variance (`ImageStat.Stat(edges).var[0]`), selecting the sharpest candidate frame with maximum local contrast and detail.

3. **Dual-Format Output & Separated Subfolder Architecture**:
   - **PNG Lossless Master (`png/`)**: Full native resolution (1080x1920 Full HD vertical, 2160x3840 4K, or 4000x5333 photo) preserved at `-q:v 1` without compression artifacts.
   - **WebP Web-Optimized (`webp/`)**: High visual fidelity web delivery with `-c:v libwebp -q:v 85`, yielding 85–92% file size reduction.
   - **Clean Subfolder Separation**: Assets can be organized into separate `png/` and `webp/` subdirectories per couple/collection (e.g. via `--separate-folders`), preventing mixed file clutter.
4. **Structured Portfolio Manifest Catalog**:

---

## Architecture Diagram

```
[Google Drive Link / File ID]
           │
           ├── Photo / HEIC ────────► High-Res Thumbnail Endpoint (&sz=w4000)
           └── Video (Raw/Edited) ──► Direct Usercontent Stream
                                            │
                                            ▼
                             [Virus Scan HTML Warning?]
                                            │
                                  Yes ──────┴────── No
                                   │                 │
                                   ▼                 │
                       [Form Token & Cookie Jar]     │
                                   │                 │
                                   └────────┬────────┘
                                            ▼
                                [Temporary Video Stream]
                                            │
                                            ▼
                             [FFmpeg Micro-Sampling Engine]
                               Window: [t - 0.4s ... t + 0.4s]
                                            │
                                            ▼
                             [Edge-Variance Sharpness Filter]
                               Select frame with max(variance)
                                            │
                           ┌────────────────┴────────────────┐
                           ▼                                 ▼
                 [PNG Lossless Master]            [WebP Web-Optimized]
                  (-vframes 1 -q:v 1)             (-c:v libwebp -q:v 85)
                           │                                 │
                           └────────────────┬────────────────┘
                                            ▼
                               [portfolio-manifest.json]
```

---

## CLI Usage

The skill provides a standalone CLI script located in `scripts/extract_gdrive_moments.py`:

```bash
# Extract 3 evenly-spaced sharp moments with separate png/ and webp/ subfolders
python3 /home/naufal/.pi/agent/skills/gdrive-portfolio-moment-extractor/scripts/extract_gdrive_moments.py \
  --drive-id 1pqBEUy3TJgx9uCcQdA0IKoqMa4GWFc15 \
  --output-dir ./output/couple-a \
  --prefix moment \
  --max-moments 3 \
  --format dual \
  --separate-folders
# Extract moments at explicit timestamps (in seconds)
python3 /home/naufal/.pi/agent/skills/gdrive-portfolio-moment-extractor/scripts/extract_gdrive_moments.py \
  --drive-id 1pqBEUy3TJgx9uCcQdA0IKoqMa4GWFc15 \
  --output-dir ./output/couple-a \
  --prefix akad \
  --timestamps 15.5 30.2 45.8 \
  --format dual

# Download and convert high-resolution photo (HEIC/JPG)
python3 /home/naufal/.pi/agent/skills/gdrive-portfolio-moment-extractor/scripts/extract_gdrive_moments.py \
  --drive-id 15HQ7UdMPtaeXOQJ0Nt0PwTEMrApWpb99 \
  --output-dir ./output/couple-a \
  --prefix moment_01_photo \
  --photo \
  --format dual
```

### CLI Parameters

| Flag | Type | Default | Description |
|---|---|---|---|
| `--drive-id` | string | *required* | Google Drive file ID or full sharing URL |
| `--output-dir` | string | `./output` | Target folder for exported assets |
| `--prefix` | string | `moment` | Output filename prefix |
| `--max-moments` | int | `3` | Number of moments to extract (evenly distributed) |
| `--timestamps` | float[] | None | Explicit timestamps in seconds (overrides `--max-moments`) |
| `--sample-window` | float | `0.4` | Micro-sampling search range ($\pm$ seconds) |
| `--steps` | int | `5` | Candidate frames evaluated in the sample window |
| `--format` | string | `dual` | Export format: `dual` (PNG + WebP), `png`, or `webp` |
| `--photo` | flag | `false` | Enable high-res photo download mode via thumbnail render |
| `--separate-folders` | flag | `false` | Segregate dual exports into dedicated `png/` and `webp/` subdirectories |
---

## Programmatic Python Integration

```python
import sys
sys.path.insert(0, '/home/naufal/.pi/agent/skills/gdrive-portfolio-moment-extractor/scripts')
from extract_gdrive_moments import (
    download_gdrive_video,
    download_gdrive_photo,
    extract_sharp_frame
)

# 1. Download video
video_path = "/tmp/my_video.mp4"
download_gdrive_video("1pqBEUy3TJgx9uCcQdA0IKoqMa4GWFc15", video_path)

# 2. Extract sharp frame at 15.5 seconds
result = extract_sharp_frame(
    video_path=video_path,
    target_time=15.5,
    out_png="./moment_01.png",
    out_webp="./moment_01.webp",
    search_window=0.4,
    steps=5,
    fmt="dual"
)

print(f"Extracted at {result['timestamp']} ({result['resolution']}), sharpness {result['sharpness']}")
```

---

## Best Practices & Troubleshooting

1. **Transient Storage Management**:
   Always clean up temporary video files (`/tmp/*.mp4`) immediately after frame extraction is completed to prevent disk exhaustion when processing large footage batches.

2. **Micro-Sampling Step Size**:
   A search window of $\pm 0.4$ seconds with 5 steps ($\sim 0.2$s intervals) reliably catches pause moments between movements without causing noticeable extraction delay.

3. **HEIC Decoding Independence**:
   Using `https://drive.google.com/thumbnail?id={id}&sz=w4000` offloads HEIC decoding to Google's rendering engine, delivering pristine JPEG frames up to 4000px wide without requiring `libheif` or `heif-convert` on the local machine.
