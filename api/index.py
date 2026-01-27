import os
import psycopg2
from flask import Flask, request, jsonify, render_template_string
from googleapiclient.discovery import build

app = Flask(__name__)

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

# --- THE "YouTube Muted" DASHBOARD ---
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Basey YT | Intelligence</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background-color: #0f0f0f; color: #f1f1f1; }
        .yt-card { background-color: #1e1e1e; border: 1px solid #333; }
        .yt-red { background-color: #ff0000; }
        .yt-muted { color: #aaaaaa; }
    </style>
</head>
<body class="min-h-screen p-4 md:p-8 font-sans">
    <div class="max-w-3xl mx-auto">
        <header class="flex justify-between items-center mb-10">
            <h1 class="text-2xl font-bold flex items-center gap-2">
                <span class="text-red-600">●</span> Basey YT
            </h1>
            <button onclick="triggerScout()" id="scoutBtn" class="text-[10px] tracking-widest uppercase font-bold text-gray-500 hover:text-white transition-all">Manual Rescan</button>
        </header>

        <div class="yt-card rounded-2xl p-6 mb-8">
            <div class="flex items-start gap-4">
                <div class="w-10 h-10 rounded-full bg-red-600/20 flex items-center justify-center text-red-500 font-bold">B</div>
                <div class="flex-1">
                    <p class="text-xs font-bold text-red-500 uppercase mb-1">Agent Intelligence</p>
                    <div id="agentChat" class="text-sm leading-relaxed text-gray-300">
                        Analyzing YouTube environment... I am currently tracking 10 insurance competitors. I have identified 3 specific outliers that are "Winning" based on engagement velocity.
                    </div>
                </div>
            </div>
        </div>

        <div class="space-y-4">
            <h3 class="text-sm font-bold text-gray-500 uppercase tracking-widest mb-4">Strategic Action Feed</h3>
            <div id="feed" class="grid gap-3">
                </div>
        </div>

        <div id="toast" class="fixed bottom-10 left-1/2 -translate-x-1/2 yt-card px-6 py-3 rounded-full text-sm font-bold hidden border-red-600/50 shadow-2xl">
            Scan Complete. Memory Updated.
        </div>
    </div>

    <div id="modal" class="hidden fixed inset-0 bg-black/90 flex items-center justify-center p-4 z-50">
        <div class="yt-card p-8 rounded-2xl max-w-lg w-full">
            <h2 class="text-xl font-bold mb-4">Content Direction</h2>
            <pre id="scriptContent" class="text-xs text-gray-400 whitespace-pre-wrap bg-black/50 p-4 rounded-xl mb-6 font-mono"></pre>
            <button onclick="closeModal()" class="w-full py-3 yt-muted bg-neutral-800 hover:bg-neutral-700 rounded-xl font-bold transition-all">Dismiss</button>
        </div>
    </div>

    <script>
        async function triggerScout() {
            const btn = document.getElementById('scoutBtn');
            const toast = document.getElementById('toast');
            btn.innerText = "Scanning...";
            try { 
                await fetch('/api/scout'); 
                toast.classList.remove('hidden');
                setTimeout(() => toast.classList.add('hidden'), 3000);
                loadAnalysis(); 
            } finally { btn.innerText = "Manual Rescan"; }
        }

        async function loadAnalysis() {
            const feed = document.getElementById('feed');
            const chat = document.getElementById('agentChat');
            try {
                const res = await fetch('/api/analyze');
                const data = await res.json();
                
                // Update Chat based on findings
                chat.innerText = `I've analyzed the niche. "${data[0].title}" is the primary growth outlier. I recommend prioritizing a remix of this hook to capture current search momentum in the Texas area.`;

                feed.innerHTML = data.slice(0, 3).map(item => `
                    <div class="yt-card p-5 rounded-xl flex justify-between items-center group hover:bg-[#2a2a2a] transition-all">
                        <div>
                            <div class="flex items-center gap-2 mb-1">
                                <span class="w-1.5 h-1.5 bg-red-600 rounded-full"></span>
                                <span class="text-[10px] font-bold uppercase tracking-widest text-gray-500 group-hover:text-red-500">${item.rec}</span>
                            </div>
                            <h4 class="text-md font-medium text-gray-200">${item.title}</h4>
                        </div>
                        <button onclick="generateVideo('${item.title}')" class="px-5 py-2.5 bg-white text-black hover:bg-gray-200 rounded-lg text-xs font-bold transition-all">Generate Video</button>
                    </div>`).join('');
            } catch (e) { feed.innerHTML = "Syncing memory..."; }
        }

        function generateVideo(title) {
            const modal = document.getElementById('modal');
            const content = document.getElementById('scriptContent');
            content.innerText = "LLM ANALYSIS FOR: " + title + "\\n\\nHOOK: 'Why every Texan is googling {topic} right now...'\\n\\nSCRIPT: Focusing on rate comparisons for 2026. Keep energy high for first 3 seconds.";
            modal.classList.remove('hidden');
        }
        function closeModal() { document.getElementById('modal').classList.add('hidden'); }
        loadAnalysis();
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/scout', methods=['GET'])
def run_scout():
    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY, cache_discovery=False)
        # We use a broad search to fill the 'Discovery' phase
        request = youtube.search().list(q="Texas life insurance tips", part="snippet", type="video", maxResults=10, order="viewCount")
        response = request.execute()
        conn = get_db_connection(); cur = conn.cursor()
        for item in response.get('items', []):
            cur.execute("INSERT INTO youtube_benchmarks (video_id, title) VALUES (%s, %s) ON CONFLICT (video_id) DO NOTHING;", (item['id']['videoId'], item['snippet']['title']))
        conn.commit(); cur.close(); conn.close()
        return jsonify({"status": "Success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze', methods=['GET'])
def get_analysis():
    try:
        conn = get_db_connection(); cur = conn.cursor()
        # Ensure we only grab 3 to fit the new design requirement
        cur.execute("SELECT title, agent_recommendation FROM v_strategic_benchmarks ORDER BY engagement_rate DESC LIMIT 3")
        rows = cur.fetchall()
        analysis = [{"title": r[0], "rec": r[1]} for r in rows]
        cur.close(); conn.close()
        return jsonify(analysis)
    except Exception as e:
        return jsonify([])

if __name__ == "__main__":
    app.run()