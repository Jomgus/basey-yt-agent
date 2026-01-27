import os
import psycopg2
from flask import Flask, request, jsonify
from googleapiclient.discovery import build

app = Flask(__name__)

# --- STEP 1: CREDENTIALS ---
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    # Neon requires sslmode=require for cloud connections
    return psycopg2.connect(DATABASE_URL, sslmode='require')

# --- STEP 2: DISCOVERY (SCOUT) ---
@app.route('/api/scout', methods=['GET'])
def run_scout():
    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY, cache_discovery=False)
        request = youtube.search().list(
            q="Texas life insurance tips",
            part="snippet",
            type="video",
            maxResults=10,
            order="viewCount"
        )
        response = request.execute()

        conn = get_db_connection()
        cur = conn.cursor()
        for item in response.get('items', []):
            cur.execute("""
                INSERT INTO youtube_benchmarks (video_id, title)
                VALUES (%s, %s) ON CONFLICT (video_id) DO NOTHING;
            """, (item['id']['videoId'], item['snippet']['title']))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "Success", "message": "Scout identified 10 new competitors."})
    except Exception as e:
        return jsonify({"error": f"Scout failed: {str(e)}"}), 500

# --- STEP 3: STRATEGIC ANALYSIS ---
@app.route('/api/analyze', methods=['GET'])
def get_analysis():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # Querying the Success View you created in Neon
        cur.execute("SELECT title, agent_recommendation FROM v_strategic_benchmarks LIMIT 5")
        rows = cur.fetchall()
        
        analysis = [{"title": r[0], "rec": r[1]} for r in rows]
        cur.close()
        conn.close()
        return jsonify(analysis)
    except Exception as e:
        # Fallback if the view isn't populated yet
        return jsonify([{"title": "Initial discovery required...", "rec": "WAITING"}])

