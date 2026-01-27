import os
import psycopg2
from flask import Flask, request, jsonify
from googleapiclient.discovery import build

# --- STEP 1: INITIALIZE APP FIRST ---
app = Flask(__name__)

# --- STEP 2: IMPORTS ---
try:
    # This relative import is required for Vercel's structure
    from .scout import scout_competitors
except ImportError:
    # Fallback for local testing
    from scout import scout_competitors

# Credentials
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

# --- STEP 3: ROUTES ---
@app.route('/api/scout', methods=['GET'])
def run_scout():
    try:
        scout_competitors()
        return jsonify({"status": "Success", "message": "Scout synced competitors to Neon."})
    except Exception as e:
        return jsonify({"error": f"Scout failed: {str(e)}"}), 500

@app.route('/api/sync', methods=['GET'])
def sync_data():
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
        """, (video_id, title, int(stats.get('viewCount', 0)), int(stats.get('likeCount', 0)), int(stats.get('commentCount', 0))))
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"status": "success", "video": title})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    return "Agent Brain is Online. Use /api/scout to discover trends."