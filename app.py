import os
import sys
import io
import json
import shutil
import traceback
import subprocess
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

app_dir = os.path.dirname(os.path.abspath(__file__))
outputs_dir = os.path.join(app_dir, "outputs")
os.makedirs(outputs_dir, exist_ok=True)

ffmpeg_bin = shutil.which("ffmpeg") or r"C:\Users\user\AppData\Local\Programs\Python\Python312\Scripts\ffmpeg.EXE"

def separate_audio_demucs_bulletproof(input_file_path):
    pcm_wav_path = os.path.join(outputs_dir, "input_converted.wav")
    print(f"[STEP 1] Converting input audio to PCM WAV: {input_file_path}")
    
    cmd_ffmpeg = [ffmpeg_bin, "-y", "-i", input_file_path, "-ac", "2", "-ar", "44100", "-c:a", "pcm_s16le", pcm_wav_path]
    res_f = subprocess.run(cmd_ffmpeg, capture_output=True, text=True)
    if res_f.returncode != 0:
        raise RuntimeError(f"FFmpeg input error: {res_f.stderr}")

    print("[STEP 2] Running Meta HT-Demucs AI Neural Network Separation...")
    cmd_demucs = [
        sys.executable, "-m", "demucs.separate",
        "-n", "htdemucs",
        "--two-stems", "vocals",
        "-o", outputs_dir,
        pcm_wav_path
    ]
    res_d = subprocess.run(cmd_demucs, capture_output=True, text=True)
    if res_d.returncode != 0:
        raise RuntimeError(f"Demucs error: {res_d.stderr}")

    htdemucs_dir = os.path.join(outputs_dir, "htdemucs", "input_converted")
    v_wav = os.path.join(htdemucs_dir, "vocals.wav")
    i_wav = os.path.join(htdemucs_dir, "no_vocals.wav")

    v_mp3 = os.path.join(htdemucs_dir, "vocals_320k.mp3")
    i_mp3 = os.path.join(htdemucs_dir, "instrumental_320k.mp3")

    print("[STEP 3] Compressing isolated stems to 320 kbps High-Quality MP3...")
    cmd_cv_v = [ffmpeg_bin, "-y", "-i", v_wav, "-b:a", "320k", v_mp3]
    cmd_cv_i = [ffmpeg_bin, "-y", "-i", i_wav, "-b:a", "320k", i_mp3]

    subprocess.run(cmd_cv_v, check=True)
    subprocess.run(cmd_cv_i, check=True)

    print(f"SUCCESS: Vocals MP3 Size: {os.path.getsize(v_mp3)} bytes")
    print(f"SUCCESS: Instrumental MP3 Size: {os.path.getsize(i_mp3)} bytes")

    return v_mp3, i_mp3

class VocalAppHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ['/', '/index.html']:
            content = open(os.path.join(app_dir, "index.html"), "rb").read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return
        
        if parsed.path.startswith('/outputs/'):
            rel_p = parsed.path.replace('/outputs/', '')
            fpath = os.path.join(outputs_dir, rel_p.replace('/', os.sep))
            if os.path.exists(fpath):
                ext = os.path.splitext(fpath)[1].lower()
                ctype = 'audio/mpeg' if ext == '.mp3' else 'audio/wav'
                content = open(fpath, "rb").read()
                self.send_response(200)
                self.send_header('Content-Type', ctype)
                self.send_header('Content-Length', str(len(content)))
                self.send_header('Accept-Ranges', 'bytes')
                self.end_headers()
                self.wfile.write(content)
                return

        self.send_error(404)

    def do_POST(self):
        if self.path == '/api/separate':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            temp_in = os.path.join(outputs_dir, "new_user_uploaded_song.audio")
            with open(temp_in, "wb") as f:
                f.write(body)
            
            try:
                v_path, i_path = separate_audio_demucs_bulletproof(temp_in)
                rel_v = os.path.relpath(v_path, outputs_dir).replace('\\', '/')
                rel_i = os.path.relpath(i_path, outputs_dir).replace('\\', '/')
                
                res = {
                    "status": "success",
                    "vocals_url": "/outputs/" + rel_v,
                    "instrumental_url": "/outputs/" + rel_i
                }
                res_bytes = json.dumps(res).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(res_bytes)))
                self.end_headers()
                self.wfile.write(res_bytes)
                print("SUCCESS: Separated & Compressed new song with Meta HT-Demucs AI!")
            except Exception as e:
                err_msg = traceback.format_exc()
                print("ERROR processing upload:", err_msg)
                err_res = json.dumps({"error": str(e), "trace": err_msg}).encode('utf-8')
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(err_res)))
                self.end_headers()
                self.wfile.write(err_res)

print("Starting Multi-Threaded Meta HT-Demucs AI Vocal Studio on http://localhost:5001 ...")
httpd = ThreadingHTTPServer(('0.0.0.0', 5001), VocalAppHandler)
httpd.serve_forever()
