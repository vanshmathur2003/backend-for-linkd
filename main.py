import os
import io
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from yt_dlp import YoutubeDL
import moviepy.editor as mp
import whisper

app = Flask(__name__)
CORS(app) 

def download_reel(url):
    ydl_opts = {
        'format': 'best',
        'outtmpl': '%(id)s.%(ext)s',
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info_dict)
            return file_path
    except Exception as e:
        print(f"An error occurred while downloading the reel: {e}")
        return None

def extract_audio(reel_path):
    try:
        video = mp.VideoFileClip(reel_path)
        audio_path = reel_path.replace('.mp4', '.wav')
        audio = video.audio
        audio.write_audiofile(audio_path)
        print(f"Audio extracted and saved as '{audio_path}'")
        return audio_path
    except Exception as e:
        print(f"An error occurred while extracting audio: {e}")
        return None

def audio_to_text(audio_file_path):
    try:
        model = whisper.load_model('base')
        result = model.transcribe(audio_file_path, fp16=False)
        return result['text']
    except Exception as e:
        print(f"An error occurred while transcribing audio: {e}")
        return None

@app.route('/download/video', methods=['POST'])
def download_video():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({"error": "URL is required"}), 400
    
    video_path = download_reel(url)
    
    if video_path:
        return send_file(video_path, as_attachment=True, download_name='video.mp4')

    return jsonify({"error": "Failed to download the video"}), 500

@app.route('/download/audio', methods=['POST'])
def download_audio():
    data = request.json
    url = data.get('url') 
    
    if not url:
        return jsonify({"error": "URL is required"}), 400
    
    video_path = download_reel(url)
    
    if video_path:
        audio_path = extract_audio(video_path)
        if audio_path:
            return send_file(audio_path, as_attachment=True, download_name='audio.wav')

    return jsonify({"error": "Failed to download or extract audio"}), 500

@app.route('/download/subtitles', methods=['POST'])
def download_subtitles():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({"error": "URL is required"}), 400
    
    video_path = download_reel(url)
    
    if video_path:
        audio_path = extract_audio(video_path)
        if audio_path:
            subtitles_text = audio_to_text(audio_path)
            if subtitles_text is not None:
                subtitles_io = io.StringIO(subtitles_text)
                subtitles_io.seek(0)
                
                subtitles_bytes_io = io.BytesIO(subtitles_io.getvalue().encode())
                subtitles_bytes_io.seek(0)
                
                return send_file(subtitles_bytes_io, as_attachment=True, download_name='subtitles.txt', mimetype='text/plain')

    return jsonify({"error": "Failed to download or process subtitles"}), 500

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=4000)