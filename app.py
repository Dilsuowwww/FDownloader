from flask import Flask, render_template, request, jsonify, send_file, abort
from yt_dlp import YoutubeDL
import os
import tempfile

app = Flask(__name__)

def get_video_info(url):
    ydl_opts = {'quiet': True, 'skip_download': True}
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    return info

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/load_info', methods=['POST'])
def load_info():
    url = request.json.get('url')
    if not url:
        return jsonify({'error': 'URL tidak boleh kosong'}), 400
    try:
        info = get_video_info(url)
        return jsonify({
            'title': info.get('title'),
            'duration': info.get('duration'),
            'thumbnail': info.get('thumbnail'),
            'uploader': info.get('uploader'),
        })
    except Exception as e:
        return jsonify({'error': f'Gagal mengambil info: {str(e)}'}), 500

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    format_choice = data.get('format')
    # folder input dari user cuma buat label, download server-side lalu dikirim file langsung ke browser (HP)
    if not url or not format_choice:
        return jsonify({'error': 'URL dan format harus diisi'}), 400

    ydl_opts = {
        'quiet': True,
        'outtmpl': os.path.join(tempfile.gettempdir(), '%(title)s.%(ext)s'),
        'noplaylist': True,
    }

    if format_choice == 'mp3':
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    else:
        ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        ydl_opts['merge_output_format'] = 'mp4'

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if format_choice == 'mp3':
                filename = os.path.splitext(filename)[0] + '.mp3'
        
        return send_file(filename, as_attachment=True)
    except Exception as e:
        return jsonify({'error': f'Gagal download: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)