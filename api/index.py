import os
import psycopg2
from flask import Flask, request, jsonify
from googleapiclient.discovery import build
# IMPORTANT: Ensure scout.py is in the same /api folder
try:
    from .scout import scout_competitors
except ImportError:
    # This handles local testing vs Vercel production
    from scout import scout_competitors

app = Flask(__name__)

# Credentials from Vercel Environment Variables
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

@app.route('/api/scout', methods=['GET'])
def run_scout():
    """Trigger the passive competitor discovery"""
    try:
        scout_competitors()
        return jsonify({
            "status": "Success", 
            "message": "Scout has identified new competitors and saved them to Neon."
        })
    except Exception as e:
        return jsonify({"error": f"Scout failed: {str(e)}"}), 500

@app.route('/api/sync', methods=['GET'])
def sync_data():
    """Manually sync metrics for a specific video ID"""
    video_id = request.args.get('video_id', 'C6a7iLnAMlQ')
    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY, cache_discovery=False)
        yt_request = youtube.videos().list(part="snippet,statistics", id=video_id)
        response = yt_request.execute()

        if not response['items']:
            return jsonify({"error": "Video not found"}), 404

        stats = response['items'][0]['statistics']
        title = response['items'][0]['snippet']['title']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO youtube_video_metrics (video_id, title, view_count, like_count, comment_count)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (video_id, captured_at) DO UPDATE SET view_count = EXCLUDED.view_count;
        """, (video_id, title, int(stats.get('viewCount', 0)), int(stats.get('like_count', 0)), int(stats.get('comment_count', 0))))
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"status": "success", "video": title, "msg": "Metrics updated in Neon"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    return "Agent is Online. Use /api/scout to find competitors or /api/sync to track metrics."