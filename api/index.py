import os
import psycopg2
from flask import Flask, request, jsonify, render_template_string
from googleapiclient.discovery import build

app = Flask(__name__)

# --- CONFIG ---
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

# --- THE HTML DASHBOARD (Stored as a Python String) ---
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Basey YT | Strategic Analyst</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-900 text-white min-h-screen p-6 md:p-12">
    <div class="max-w-4xl mx-auto">
        <header class="flex justify-between items-center mb-12">
            <div>
                <h1 class="text-4xl font-extrabold text-blue-400 tracking-tight">Basey YT</h1>
                <p class="text-slate-400 mt-1">Strategic Analyst Agent • V1.0 Prototype</p>
            </div>
            <span class="px-3 py-1 rounded-full bg-blue-500/10 text-blue-400 text-xs font-mono border border-blue-500/20">AGENT_ACTIVE</span>
        </header>

        <div class="bg-slate-800/50 rounded-2xl p-6 border border-slate-700 mb-8 flex items-center justify-between">
            <div class="text-sm text-slate-400">
                <span class="font-bold text-slate-200">Passive Discovery:</span> Agent is currently scouting "Texas Life Insurance" trends.
            </div>
            <button onclick="triggerScout()" id="scoutBtn" class="text-xs bg-slate-700 hover:bg-slate-600 px-4 py-2 rounded-lg transition-all">Manual Rescan</button>
        </div>

        <div class="grid grid-cols-1 gap-6">
            <h3 class="text-xl font-bold text-slate-200 flex items-center gap-2">
                <span class="w-2 h-2 bg-orange-500 rounded-full animate-pulse"></span>
                Strategic Action Feed
            </h3>
            <div id="feed" class="space-y-4">
                </div>
        </div>
    </div>
    <script>
        async function triggerScout() {
            const btn = document.getElementById('scoutBtn');
            btn.innerText = "Scouting...";
            try { await fetch('/api/scout'); loadAnalysis(); } 
            finally { btn.innerText = "Manual Rescan"; }
        }
        async function loadAnalysis() {
            const feed = document.getElementById('feed');
            try {
                const res = await fetch('/api/analyze');
                const data = await res.json();
                feed.innerHTML = data.map(item => `
                    <div class="p-6 bg-slate-800 rounded-2xl border border-slate-700 flex justify-between items-center gap-4 hover:border-blue-500/30 transition-all">
                        <div>
                            <span class="text-[10px] font-black uppercase tracking-widest text-blue-400 bg-blue-400/10 px-2 py-1 rounded-md">${item.rec}</span>
                            <h4 class="text-lg font-semibold mt-2 text-slate-100">${item.title}</h4>
                        </div>
                        <button class="px-6 py-3 bg-blue-600 hover:bg-blue-500 rounded-xl text-sm font-bold shadow-lg shadow-blue-900/20 transition-all active:scale-95">Generate Video</button>
                    </div>`).join('');
            } catch (e) { feed.innerHTML = "Priming Analyst Engine..."; }
        }
        loadAnalysis();
    </script>
</body>
</html>
"""
# --- ROUTES ---

@app.route('/')
def home():
    """Renders the dashboard directly from Python"""
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/scout', methods=['GET'])
def run_scout():
    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY, cache_discovery=False)
        request = youtube.search().list(q="Texas life insurance tips", part="snippet", type="video", maxResults=10, order="viewCount")
        response = request.execute()
        conn = get_db_connection()
        cur = conn.cursor()
        for item in response.get('items', []):
            cur.execute("INSERT INTO youtube_benchmarks (video_id, title) VALUES (%s, %s) ON CONFLICT (video_id) DO NOTHING;", (item['id']['videoId'], item['snippet']['title']))
        conn.commit()
        cur.close(); conn.close()
        return jsonify({"status": "Success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze', methods=['GET'])
def get_analysis():
    try:
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("SELECT title, agent_recommendation FROM v_strategic_benchmarks ORDER BY engagement_rate DESC LIMIT 3")
        rows = cur.fetchall()
        analysis = [{"title": r[0], "rec": r[1]} for r in rows]
        cur.close(); conn.close()
        return jsonify(analysis)
    except Exception as e:
        return jsonify([])

if __name__ == "__main__":
    app.run()