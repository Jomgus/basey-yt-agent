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
        body { background-color: #1a1a1b; color: #d7dadc; }
        .yt-card { background-color: #272729; border: 1px solid #343536; }
        .prompt-btn { background-color: #343536; border: 1px solid #474849; }
        .prompt-btn:hover { background-color: #474849; border-color: #818384; }
    </style>
</head>
<body class="min-h-screen p-4 md:p-8 font-sans">
    <div class="max-w-4xl mx-auto">
        
        <header class="flex justify-between items-center mb-10">
            <h1 class="text-xl font-bold flex items-center gap-2 tracking-tight">
                <span class="text-red-500 text-2xl">■</span> BASEY YT
            </h1>
            <button onclick="triggerScout()" id="scoutBtn" class="text-[10px] tracking-widest uppercase font-bold text-gray-500 hover:text-white transition-all">Manual Rescan</button>
        </header>

        <div class="mb-12">
            <p class="text-[10px] font-bold text-gray-500 uppercase tracking-[0.2em] mb-4">Recommended Strategic Actions</p>
            <div id="promptContainer" class="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div class="prompt-btn p-4 rounded-xl text-xs text-gray-400 animate-pulse text-center">Analyst is generating prompts...</div>
            </div>
        </div>

        <div class="space-y-4">
            <h3 class="text-[10px] font-bold text-gray-500 uppercase tracking-[0.2em] mb-4">High-Velocity Targets</h3>
            <div id="feed" class="grid gap-2">
                </div>
        </div>

        <div id="toast" class="fixed bottom-10 left-1/2 -translate-x-1/2 yt-card px-8 py-4 rounded-2xl text-sm font-bold hidden border-red-500/30 shadow-2xl transition-all">
            ✅ Scan Complete. Intelligence Refreshed.
        </div>
    </div>

    <div id="modal" class="hidden fixed inset-0 bg-black/60 backdrop-blur-md flex items-center justify-center p-4 z-50">
        <div class="yt-card p-8 rounded-3xl max-w-lg w-full shadow-2xl">
            <h2 class="text-xl font-bold mb-4 text-white">Agent Output</h2>
            <pre id="scriptContent" class="text-xs text-gray-400 whitespace-pre-wrap bg-black/30 p-5 rounded-2xl mb-6 font-mono border border-white/5"></pre>
            <button onclick="closeModal()" class="w-full py-4 bg-white text-black rounded-2xl font-bold hover:bg-gray-200 transition-all">Dismiss</button>
        </div>
    </div>

    <script>
        async function triggerScout() {
            const btn = document.getElementById('scoutBtn');
            const toast = document.getElementById('toast');
            btn.innerText = "SCANNING...";
            try { 
                await fetch('/api/scout'); 
                toast.classList.remove('hidden');
                setTimeout(() => toast.classList.add('hidden'), 3000);
                loadAnalysis(); 
            } finally { btn.innerText = "MANUAL RESCAN"; }
        }

        async function loadAnalysis() {
            const feed = document.getElementById('feed');
            const prompts = document.getElementById('promptContainer');
            
            try {
                const res = await fetch('/api/analyze');
                const data = await res.json();
                
                // Inject Top 3 Strategic Prompts (Mocked logic for demo)
                const topVideo = data[0].title;
                prompts.innerHTML = `
                    <button onclick="generateAction('Draft a counter-script for ${topVideo}')" class="prompt-btn p-4 rounded-xl text-left text-xs font-medium hover:text-white transition-all">
                        "Draft a counter-script for the ${topVideo.substring(0,20)}... trend."
                    </button>
                    <button onclick="generateAction('Analyze why ${topVideo} is winning')" class="prompt-btn p-4 rounded-xl text-left text-xs font-medium hover:text-white transition-all">
                        "Analyze why '${topVideo.substring(0,20)}...' is currently winning."
                    </button>
                    <button onclick="generateAction('Generate 3 Texas Hook variations')" class="prompt-btn p-4 rounded-xl text-left text-xs font-medium hover:text-white transition-all">
                        "Generate 3 Texas-specific 'Hook' variations for this niche."
                    </button>
                `;

                feed.innerHTML = data.slice(0, 3).map(item => `
                    <div class="yt-card p-5 rounded-2xl flex justify-between items-center group hover:border-gray-500 transition-all">
                        <div>
                            <div class="flex items-center gap-2 mb-1">
                                <span class="text-[9px] font-black uppercase tracking-widest text-red-500">${item.rec}</span>
                            </div>
                            <h4 class="text-sm font-medium text-gray-200">${item.title}</h4>
                        </div>
                        <button onclick="generateAction('Full Video Script for: ${item.title}')" class="px-5 py-2.5 bg-white text-black hover:bg-gray-200 rounded-xl text-[10px] font-black uppercase tracking-tighter transition-all">Generate Video</button>
                    </div>`).join('');
            } catch (e) { feed.innerHTML = "Syncing memory..."; }
        }

        function generateAction(action) {
            const modal = document.getElementById('modal');
            const content = document.getElementById('scriptContent');
            content.innerText = "AGENT BRAIN // STRATEGIC OUTPUT\\n\\nACTION: " + action + "\\n\\nRESULT: [The LLM will generate the full script or analysis here based on the data in Neon SQL.]";
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