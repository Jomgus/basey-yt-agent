
import os
import psycopg2
from flask import Flask, request, jsonify
from googleapiclient.discovery import build

@app.route('/api/scout', methods=['GET'])
def run_scout():
    # Trigger your scout logic here
    from .scout import scout_competitors # Assuming scout.py is in the same folder
    scout_competitors()
    return jsonify({"status": "Scout triggered successfully"})


app = Flask(__name__)

# Use the Environment Variable in Vercel, or this fallback for now
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "AIzaSyBoStG3HWUr31_X1dMpJ7oU6cyo0eY_rzg")
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

@app.route('/api/sync', methods=['GET'])
def sync_data():
    video_id = request.args.get('video_id', 'C6a7iLnAMlQ')
    try:
        # 1. Fetch from YouTube
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY, cache_discovery=False)
        yt_request = youtube.videos().list(part="snippet,statistics", id=video_id)
        response = yt_request.execute()

        if not response['items']:
            return jsonify({"error": "Video not found"}), 404

        stats = response['items'][0]['statistics']
        title = response['items'][0]['snippet']['title']

        # 2. Save to Neon
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO youtube_video_metrics (video_id, title, view_count, like_count, comment_count)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (video_id, captured_at) DO UPDATE SET view_count = EXCLUDED.view_count;
        """, (video_id, title, int(stats.get('viewCount', 0)), int(stats.get('likeCount', 0)), int(stats.get('commentCount', 0))))
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"status": "success", "video": title})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# This is the "Entrypoint" Vercel looks for
@app.route('/')
def home():
    return "Agent is Online. Use /api/sync to trigger discovery."