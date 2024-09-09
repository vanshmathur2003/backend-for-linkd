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
        'outtmpl': 'video.%(ext)s',  # Save video temporarily in memory
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info_dict)
            with open(file_path, 'rb') as file:
                file_content = file.read()
            os.remove(file_path)  # Remove the file after reading its content
            return file_content
    except Exception as e:
        print(f"An error occurred while downloading the reel: {e}")
        return None

def extract_audio(video_content):
    try:
        video = mp.VideoFileClip(io.BytesIO(video_content))
        audio_path = io.BytesIO()
        audio = video.audio
        audio.write_audiofile(audio_path)
        audio_path.seek(0)
        print("Audio extracted and saved in memory")
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
    
    video_content = download_reel(url)
    
    if video_content:
        return send_file(io.BytesIO(video_content), as_attachment=True, download_name='video.mp4', mimetype='video/mp4')

    return jsonify({"error": "Failed to download the video"}), 500

@app.route('/download/audio', methods=['POST'])
def download_audio():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({"error": "URL is required"}), 400
    
    video_content = download_reel(url)
    
    if video_content:
        audio_path = extract_audio(video_content)
        if audio_path:
            return send_file(audio_path, as_attachment=True, download_name='audio.wav', mimetype='audio/wav')

    return jsonify({"error": "Failed to download or extract audio"}), 500

@app.route('/download/subtitles', methods=['POST'])
def download_subtitles():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({"error": "URL is required"}), 400
    
    video_content = download_reel(url)
    
    if video_content:
        audio_path = extract_audio(video_content)
        if audio_path:
            subtitles_text = audio_to_text(audio_path)
            if subtitles_text is not None:
                subtitles_io = io.StringIO(subtitles_text)
                return send_file(io.BytesIO(subtitles_io.getvalue().encode()), as_attachment=True, download_name='subtitles.txt', mimetype='text/plain')

    return jsonify({"error": "Failed to download or process subtitles"}), 500

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=4000)
