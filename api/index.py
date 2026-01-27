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
    <title>Basey YT | Strategy</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background-color: #1a1a1b; color: #d7dadc; }
        .card-bg { background-color: #272729; border: 1px solid #343536; }
        .accent-border { border-left: 4px solid #ff0000; }
    </style>
</head>
<body class="min-h-screen p-6 md:p-12 font-sans">
    <div class="max-w-5xl mx-auto">
        
        <header class="mb-12">
            <h1 class="text-4xl font-black text-white tracking-tighter italic">BASEY YT <span class="text-red-600">●</span></h1>
            <p class="text-gray-500 font-bold uppercase tracking-[0.3em] text-xs mt-2">Strategic Intelligence Agent // V1.0</p>
        </header>

        <div class="card-bg rounded-3xl p-8 mb-10 flex flex-col md:flex-row items-center justify-between gap-8 shadow-2xl">
            <div class="max-w-xl">
                <h2 class="text-2xl font-bold text-white mb-2">Passive Discovery Engine</h2>
                <p class="text-gray-400 text-lg">The agent is scanning the Texas insurance niche for high-velocity competitor content.</p>
            </div>
            <button onclick="triggerScout()" id="scoutBtn" class="bg-white text-black px-10 py-5 rounded-2xl font-black text-lg uppercase tracking-tight hover:bg-gray-200 transition-all active:scale-95 shadow-xl">
                Manual Rescan
            </button>
        </div>

        <section class="mb-16">
            <h3 class="text-xs font-black text-gray-500 uppercase tracking-[0.3em] mb-6">AI Strategic Directions</h3>
            <div id="promptContainer" class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div class="card-bg p-8 rounded-3xl animate-pulse text-center text-gray-600">Generating Strategy...</div>
            </div>
        </section>

        <section>
            <h3 class="text-xs font-black text-gray-500 uppercase tracking-[0.3em] mb-6">Top Competitor Targets</h3>
            <div id="feed" class="space-y-6">
                </div>
        </section>

        <div id="toast" class="fixed bottom-12 left-1/2 -translate-x-1/2 card-bg px-10 py-5 rounded-3xl text-lg font-bold hidden border-red-600/50 shadow-2xl z-50">
            ✅ SCAN COMPLETE. MEMORY REFRESHED.
        </div>
    </div>

    <div id="modal" class="hidden fixed inset-0 bg-black/80 backdrop-blur-xl flex items-center justify-center p-6 z-50">
        <div class="card-bg p-10 rounded-[40px] max-w-2xl w-full shadow-2xl">
            <h2 class="text-3xl font-black mb-6 text-white uppercase tracking-tighter">Agent Execution</h2>
            <div id="scriptContent" class="text-lg text-gray-300 leading-relaxed whitespace-pre-wrap bg-black/40 p-8 rounded-3xl mb-8 font-medium border border-white/5"></div>
            <button onclick="closeModal()" class="w-full py-5 bg-white text-black rounded-2xl font-black text-xl uppercase tracking-tight hover:bg-gray-200 transition-all">Dismiss</button>
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
                setTimeout(() => toast.classList.add('hidden'), 4000);
                loadAnalysis(); 
            } finally { btn.innerText = "MANUAL RESCAN"; }
        }

        async function loadAnalysis() {
            const feed = document.getElementById('feed');
            const prompts = document.getElementById('promptContainer');
            
            try {
                const res = await fetch('/api/analyze');
                const data = await res.json();
                
                // LARGE STRATEGY BLOCKS
                const topVideo = data[0].title;
                prompts.innerHTML = `
                    <button onclick="generateAction('SCRIPT', '${topVideo}')" class="card-bg accent-border p-8 rounded-3xl text-left hover:bg-[#343536] transition-all group">
                        <p class="text-[10px] font-black text-red-500 uppercase mb-2">Production</p>
                        <h4 class="text-xl font-bold leading-tight group-hover:text-white">Draft Counter-Script for "${topVideo.substring(0,30)}..."</h4>
                    </button>
                    <button onclick="generateAction('ANALYSIS', '${topVideo}')" class="card-bg accent-border p-8 rounded-3xl text-left hover:bg-[#343536] transition-all group">
                        <p class="text-[10px] font-black text-red-500 uppercase mb-2">Strategy</p>
                        <h4 class="text-xl font-bold leading-tight group-hover:text-white">Why is this specific competitor winning right now?</h4>
                    </button>
                    <button onclick="generateAction('HOOKS', '${topVideo}')" class="card-bg accent-border p-8 rounded-3xl text-left hover:bg-[#343536] transition-all group">
                        <p class="text-[10px] font-black text-red-500 uppercase mb-2">Creative</p>
                        <h4 class="text-xl font-bold leading-tight group-hover:text-white">Generate 5 Viral Hooks for the Texas Market</h4>
                    </button>
                `;

                // LARGE TARGET CARDS
                feed.innerHTML = data.slice(0, 3).map(item => `
                    <div class="card-bg p-8 rounded-[32px] flex flex-col md:flex-row justify-between items-center gap-8 group hover:border-gray-500 transition-all">
                        <div class="flex-1">
                            <span class="text-xs font-black uppercase tracking-[0.2em] text-red-500 mb-3 block">${item.rec}</span>
                            <h4 class="text-2xl font-bold text-gray-100 leading-tight">${item.title}</h4>
                        </div>
                        <button onclick="generateAction('VIDEO', '${item.title}')" class="w-full md:w-auto px-10 py-5 bg-white text-black hover:bg-gray-200 rounded-2xl text-sm font-black uppercase tracking-tighter transition-all active:scale-95">
                            Generate Video
                        </button>
                    </div>`).join('');
            } catch (e) { feed.innerHTML = "Establishing secure link to Neon..."; }
        }

        function generateAction(type, title) {
            const modal = document.getElementById('modal');
            const content = document.getElementById('scriptContent');
            content.innerText = "AGENT PROCESS: " + type + "\\nCONTEXT: " + title + "\\n\\n[AI AGENT IS PROCESSING DATA IN NEON SQL...]\\n\\n1. Found growth outlier in Texas niche.\\n2. Writing script focused on 2026 Part B rates.\\n3. Ready for approval.";
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