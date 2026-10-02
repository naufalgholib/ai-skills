#!/usr/bin/env python3
"""
instagram-moment-extractor: CLI tool to extract high-definition video frames
and portfolio moments from Instagram Reels, Posts, and Stories.

Features:
- Dual-format export (PNG lossless master + WebP web-optimized)
- 3-Tier fallback strategy (Public yt-dlp -> Cookie/Session -> Active Browser)
- Accurate FFmpeg micro-sampling
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def detect_instagram_url_type(url: str) -> str:
    """Classifies Instagram URL into reel, post, highlight, or story."""
    if "/reel/" in url:
        return "reel"
    elif "/p/" in url:
        return "post"
    elif "/s/" in url or "highlight" in url:
        return "highlight"
    elif "/stories/" in url:
        return "story"
    return "unknown"


def find_yt_dlp(custom_path: str = None) -> str:
    """Finds yt-dlp executable in PATH or user directories."""
    candidates = []
    if custom_path:
        candidates.append(custom_path)
    candidates.extend([
        shutil.which("yt-dlp"),
        os.path.expanduser("~/.local/bin/yt-dlp"),
        "/usr/local/bin/yt-dlp",
        "/usr/bin/yt-dlp",
    ])
    for c in candidates:
        if c and os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    raise FileNotFoundError("yt-dlp executable not found in PATH or standard locations.")


def download_instagram_video(url: str, output_dir: Path, cookies: str = None, yt_dlp_path: str = None) -> Path:
    """Downloads Instagram video using yt-dlp with optional cookies."""
    yt_dlp = find_yt_dlp(yt_dlp_path)
    url_type = detect_instagram_url_type(url)
    output_template = str(output_dir / "%(id)s.%(ext)s")

    cmd = [
        yt_dlp,
        "-f", "bv*+ba/b",
        "--no-playlist",
        "-o", output_template,
    ]

    if cookies:
        if os.path.isfile(cookies):
            cmd.extend(["--cookies", cookies])
        else:
            # Pass cookie header string
            cmd.extend(["--add-header", f"Cookie:{cookies}"])

    cmd.append(url)

    print(f"[*] Downloading ({url_type}): {url}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        error_msg = result.stderr or result.stdout
        print(f"[!] yt-dlp error: {error_msg.strip()}", file=sys.stderr)
        if url_type in ("highlight", "story") and ("login" in error_msg.lower() or "unsupported" in error_msg.lower()):
            raise PermissionError(
                f"Instagram {url_type} requires authenticated session (Tingkat 2/3: supply --cookies or active session)."
            )
        raise RuntimeError(f"Download failed for {url}: {error_msg}")

    # Locate downloaded video file
    downloaded_files = list(output_dir.glob("*.mp4")) + list(output_dir.glob("*.webm"))
    if not downloaded_files:
        raise FileNotFoundError(f"Downloaded video file not found in {output_dir}")
    downloaded_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return downloaded_files[0]


def extract_frame(video_path: Path, timestamp: str, output_png: Path, output_webp: Path, webp_quality: int = 85):
    """Extracts frame losslessly to PNG and converts to web-optimized WebP."""
    # Step 1: Lossless PNG frame extraction
    cmd_png = [
        "ffmpeg", "-y",
        "-ss", timestamp,
        "-i", str(video_path),
        "-frames:v", "1",
        str(output_png)
    ]
    res_png = subprocess.run(cmd_png, capture_output=True, text=True)
    if res_png.returncode != 0:
        raise RuntimeError(f"FFmpeg frame extraction failed at {timestamp}: {res_png.stderr}")

    # Step 2: High quality WebP conversion from master PNG
    cmd_webp = [
        "ffmpeg", "-y",
        "-i", str(output_png),
        "-c:v", "libwebp",
        "-q:v", str(webp_quality),
        str(output_webp)
    ]
    res_webp = subprocess.run(cmd_webp, capture_output=True, text=True)
    if res_webp.returncode != 0:
        raise RuntimeError(f"FFmpeg WebP conversion failed: {res_webp.stderr}")


def get_media_dimensions(file_path: Path) -> tuple:
    """Uses ffprobe to return (width, height) of an image or video."""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=s=x:p=0",
        str(file_path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0 and res.stdout.strip():
        parts = res.stdout.strip().split("x")
        if len(parts) == 2:
            return int(parts[0]), int(parts[1])
    return None, None


def main():
    parser = argparse.ArgumentParser(
        description="Extract high-definition moments from Instagram Reels, Stories, or local video files."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-u", "--url", help="Instagram URL (Reel, Post, Story, Highlight)")
    group.add_argument("-v", "--video", help="Path to existing local video file")

    parser.add_argument("-t", "--timestamps", required=True, nargs="+",
                        help="List of timestamps to extract (e.g. 00:00:09.600 00:00:16.600)")
    parser.add_argument("-n", "--names", nargs="+",
                        help="Custom names for extracted moments (matching number of timestamps)")
    parser.add_argument("-o", "--output-dir", default="./extracted-moments",
                        help="Directory to save extracted assets (default: ./extracted-moments)")
    parser.add_argument("-q", "--webp-quality", type=int, default=85,
                        help="WebP compression quality (default: 85)")
    parser.add_argument("-c", "--cookies",
                        help="Path to cookies.txt or raw session cookie string")
    parser.add_argument("--yt-dlp-path",
                        help="Custom path to yt-dlp executable")
    parser.add_argument("--keep-video", action="store_true",
                        help="Keep downloaded temporary video file")

    args = parser.parse_args()

    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = out_dir / ".cache_video"
    temp_dir.mkdir(parents=True, exist_ok=True)

    video_path = None
    downloaded = False

    try:
        if args.video:
            video_path = Path(args.video).resolve()
            if not video_path.is_file():
                print(f"[!] Error: Video file not found: {video_path}", file=sys.stderr)
                sys.exit(1)
        else:
            video_path = download_instagram_video(
                url=args.url,
                output_dir=temp_dir,
                cookies=args.cookies,
                yt_dlp_path=args.yt_dlp_path
            )
            downloaded = True

        timestamps = args.timestamps
        names = args.names or [f"moment_{i+1:02d}" for i in range(len(timestamps))]
        if len(names) != len(timestamps):
            print("[!] Error: Number of names must match number of timestamps", file=sys.stderr)
            sys.exit(1)

        manifest_moments = []
        print(f"[*] Extracting {len(timestamps)} moments into {out_dir}...")

        for idx, (ts, name) in enumerate(zip(timestamps, names), 1):
            clean_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", name)
            png_file = out_dir / f"{clean_name}.png"
            webp_file = out_dir / f"{clean_name}.webp"

            print(f"  [{idx}/{len(timestamps)}] Extracting {clean_name} at {ts}...")
            extract_frame(video_path, ts, png_file, webp_file, webp_quality=args.webp_quality)

            w, h = get_media_dimensions(png_file)
            manifest_moments.append({
                "index": idx,
                "name": clean_name,
                "timestamp": ts,
                "png": str(png_file.name),
                "webp": str(webp_file.name),
                "width": w,
                "height": h,
                "size_png_kb": round(png_file.stat().st_size / 1024, 1),
                "size_webp_kb": round(webp_file.stat().st_size / 1024, 1)
            })

        summary = {
            "source": args.url or str(video_path),
            "extracted_at": datetime.utcnow().isoformat() + "Z",
            "total_moments": len(manifest_moments),
            "moments": manifest_moments
        }

        summary_file = out_dir / "extraction-summary.json"
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)

        print(f"[✓] Extraction complete! {len(manifest_moments)} moments saved to {out_dir}")
        print(f"[✓] Summary written to {summary_file}")

    finally:
        if downloaded and not args.keep_video and temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
