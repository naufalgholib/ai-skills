#!/usr/bin/env python3
"""
CLI Utility: Google Drive Portfolio Moment Extractor (gdrive-portfolio-moment-extractor)
Extracts HD frames from Google Drive videos/photos without API keys, evaluates sharpness, and exports dual-format PNG & WebP.
"""

import os
import sys
import argparse
import json
import time
import subprocess
import urllib.request
import urllib.parse
import http.cookiejar
import re
from PIL import Image, ImageFilter, ImageStat

COOKIE_JAR = http.cookiejar.CookieJar()
OPENER = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(COOKIE_JAR))
OPENER.addheaders = [('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0')]

def parse_drive_id(raw_input):
    """Extract Google Drive file ID from URL or raw ID string."""
    if not raw_input:
        return ""
    m = re.search(r'[-_\w]{25,}', raw_input)
    return m.group(0) if m else raw_input.strip()

def download_gdrive_video(file_id, dest_path, max_retries=3):
    """Download Google Drive video file, bypassing virus scan warning confirmation."""
    for attempt in range(max_retries):
        try:
            url = f'https://drive.usercontent.google.com/download?id={file_id}&export=download&authuser=0'
            resp = OPENER.open(url, timeout=45)
            
            content_type = resp.headers.get('Content-Type', '')
            if 'text/html' in content_type:
                html = resp.read().decode('utf-8', errors='ignore')
                inputs = re.findall(r'<input\s+type=\"hidden\"\s+name=\"([^\"]+)\"\s+value=\"([^\"]*)\"', html)
                if not inputs:
                    inputs = re.findall(r'<input\s+[^>]*name=\"([^\"]+)\"\s+[^>]*value=\"([^\"]*)\"', html)
                params = {k: v for k, v in inputs}
                
                action_match = re.search(r'<form\s+[^>]*action=\"([^\"]+)\"', html)
                action_url = action_match.group(1) if action_match else 'https://drive.usercontent.google.com/download'
                
                full_url = f'{action_url}?{urllib.parse.urlencode(params)}'
                resp = OPENER.open(full_url, timeout=45)
                
            with open(dest_path, 'wb') as out_f:
                while True:
                    chunk = resp.read(1024 * 1024 * 4) # 4MB
                    if not chunk:
                        break
                    out_f.write(chunk)
                    
            if os.path.exists(dest_path) and os.path.getsize(dest_path) > 100000:
                return True
        except Exception as e:
            print(f"[Warning] Download attempt {attempt+1} failed: {e}", file=sys.stderr)
            time.sleep(2)
    return False

def download_gdrive_photo(file_id, dest_path, width=4000, max_retries=3):
    """Download high-res rendered photo via Google Drive thumbnail endpoint."""
    url = f'https://drive.google.com/thumbnail?id={file_id}&sz=w{width}'
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30) as resp, open(dest_path, 'wb') as out_f:
                out_f.write(resp.read())
            if os.path.exists(dest_path) and os.path.getsize(dest_path) > 10000:
                return True
        except Exception as e:
            print(f"[Warning] Photo download attempt {attempt+1} failed: {e}", file=sys.stderr)
            time.sleep(2)
    return False

def compute_sharpness(img):
    """Calculate variance of edge filter to evaluate visual sharpness."""
    gray = img.convert('L')
    edges = gray.filter(ImageFilter.FIND_EDGES)
    return ImageStat.Stat(edges).var[0]

def extract_sharp_frame(video_path, target_time, out_png, out_webp=None, search_window=0.4, steps=5, fmt="dual"):
    """Micro-sample frames in [target_time - search_window, target_time + search_window] and select highest sharpness."""
    import io
    half_w = search_window
    step_size = (2 * half_w) / (steps - 1) if steps > 1 else 0
    
    best_time = target_time
    best_sharp = -1
    best_bytes = None
    
    for i in range(steps):
        st = target_time - half_w + i * step_size
        st = max(0.2, st)
        cmd = ['ffmpeg', '-ss', f'{st:.3f}', '-i', video_path, '-vframes', '1', '-f', 'image2pipe', '-vcodec', 'png', '-']
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        if p.stdout and len(p.stdout) > 1000:
            try:
                img = Image.open(io.BytesIO(p.stdout))
                sharpness = compute_sharpness(img)
                if sharpness > best_sharp:
                    best_sharp = sharpness
                    best_time = st
                    best_bytes = p.stdout
            except Exception:
                pass
                
    if best_bytes is None:
        subprocess.run(['ffmpeg', '-ss', f'{target_time:.3f}', '-i', video_path, '-vframes', '1', '-q:v', '1', '-y', out_png],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        with open(out_png, 'wb') as f:
            f.write(best_bytes)
            
    if fmt in ("dual", "webp") and out_webp:
        subprocess.run(['ffmpeg', '-i', out_png, '-c:v', 'libwebp', '-q:v', '85', '-y', out_webp],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if fmt == "webp" and os.path.exists(out_png):
            os.remove(out_png)
            
    w, h = 0, 0
    if fmt in ("dual", "png"):
        if not os.path.exists(out_png) or os.path.getsize(out_png) == 0:
            raise RuntimeError(f"Failed to generate PNG master at {out_png}")
        probe_png = subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'stream=width,height', '-of', 'json', out_png])
        pdata_png = json.loads(probe_png)
        w = pdata_png['streams'][0]['width']
        h = pdata_png['streams'][0]['height']

    if fmt in ("dual", "webp") and out_webp:
        if not os.path.exists(out_webp) or os.path.getsize(out_webp) == 0:
            raise RuntimeError(f"Failed to generate WebP at {out_webp}")
        probe_webp = subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'stream=width,height', '-of', 'json', out_webp])
        pdata_webp = json.loads(probe_webp)
        if not w:
            w = pdata_webp['streams'][0]['width']
            h = pdata_webp['streams'][0]['height']
    
    return {
        'timestamp': f"{int(best_time//3600):02d}:{int((best_time%3600)//60):02d}:{best_time%60:06.3f}",
        'seconds': round(best_time, 3),
        'resolution': f"{w}x{h}",
        'sharpness': round(best_sharp, 2)
    }

def main():
    parser = argparse.ArgumentParser(description="Extract HD moments from Google Drive videos/photos without API key.")
    parser.add_argument("--drive-id", required=True, help="Google Drive file ID or full URL")
    parser.add_argument("--output-dir", default="./output", help="Directory to save extracted assets")
    parser.add_argument("--prefix", default="moment", help="Output filename prefix")
    parser.add_argument("--max-moments", type=int, default=3, help="Number of moments to extract from video")
    parser.add_argument("--sample-window", type=float, default=0.4, help="Micro-sampling window (+/- seconds)")
    parser.add_argument("--steps", type=int, default=5, help="Number of micro-sampling steps")
    parser.add_argument("--format", choices=["dual", "png", "webp"], default="dual", help="Export format")
    parser.add_argument("--photo", action="store_true", help="Download as high-res photo instead of video")
    parser.add_argument("--timestamps", nargs="*", type=float, help="Explicit timestamps in seconds (overrides max-moments)")
    parser.add_argument("--separate-folders", action="store_true", help="Organize dual exports into separate png/ and webp/ subdirectories")
    args = parser.parse_args()

    file_id = parse_drive_id(args.drive_id)
    png_dir = os.path.join(args.output_dir, "png") if args.separate_folders else args.output_dir
    webp_dir = os.path.join(args.output_dir, "webp") if args.separate_folders else args.output_dir
    os.makedirs(png_dir, exist_ok=True)
    os.makedirs(webp_dir, exist_ok=True)
    temp_dir = "/tmp/gdrive_cli_temp"
    os.makedirs(temp_dir, exist_ok=True)
    
    if args.photo:
        print(f"Downloading high-res photo {file_id}...")
        tmp_jpg = os.path.join(temp_dir, f"photo_{file_id}.jpg")
        if not download_gdrive_photo(file_id, tmp_jpg):
            print(f"Error: Failed to download photo {file_id}", file=sys.stderr)
            sys.exit(1)
            
        out_png = os.path.join(png_dir, f"{args.prefix}.png")
        out_webp = os.path.join(webp_dir, f"{args.prefix}.webp")
        
        subprocess.run(['ffmpeg', '-i', tmp_jpg, '-q:v', '1', '-y', out_png],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if args.format in ("dual", "webp"):
            subprocess.run(['ffmpeg', '-i', out_png, '-c:v', 'libwebp', '-q:v', '85', '-y', out_webp],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if args.format == "webp" and os.path.exists(out_png):
            os.remove(out_png)
        if os.path.exists(tmp_jpg):
            os.remove(tmp_jpg)
            
        if args.format in ("dual", "png"):
            if not os.path.exists(out_png) or os.path.getsize(out_png) == 0:
                raise RuntimeError(f"Failed to generate PNG master at {out_png}")
            subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'stream=width,height', out_png])
        if args.format in ("dual", "webp"):
            if not os.path.exists(out_webp) or os.path.getsize(out_webp) == 0:
                raise RuntimeError(f"Failed to generate WebP at {out_webp}")
            subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'stream=width,height', out_webp])
            
        print(f"Saved photo: {out_png if args.format != 'webp' else out_webp}")
        return

    # Video Mode
    print(f"Downloading video {file_id}...")
    local_vid = os.path.join(temp_dir, f"vid_{file_id}.mp4")
    if not download_gdrive_video(file_id, local_vid):
        print(f"Error: Failed to download video {file_id}", file=sys.stderr)
        sys.exit(1)
        
    try:
        dur_out = subprocess.check_output([
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', local_vid
        ])
        duration = float(dur_out.strip())
    except Exception:
        duration = 60.0
        
    print(f"Video duration: {duration:.2f}s")
    
    if args.timestamps:
        target_times = args.timestamps
    else:
        n = args.max_moments
        target_times = [duration * (i + 1) / (n + 1) for i in range(n)]
        
    results = []
    for idx, t in enumerate(target_times):
        m_name = f"{args.prefix}_{idx+1:02d}"
        png_out = os.path.join(png_dir, f"{m_name}.png")
        webp_out = os.path.join(webp_dir, f"{m_name}.webp")
        
        print(f"Extracting moment {idx+1}/{len(target_times)} around {t:.2f}s...")
        meta = extract_sharp_frame(
            local_vid, t, png_out, webp_out,
            search_window=args.sample_window, steps=args.steps, fmt=args.format
        )
        meta["index"] = idx + 1
        meta["file_prefix"] = m_name
        results.append(meta)
        print(f"  -> Chosen {meta['timestamp']} ({meta['resolution']}), sharpness {meta['sharpness']}")
        
    if os.path.exists(local_vid):
        os.remove(local_vid)
        
    summary_path = os.path.join(args.output_dir, f"{args.prefix}_summary.json")
    with open(summary_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Complete! Extracted {len(results)} moments to {args.output_dir}")

if __name__ == "__main__":
    main()
