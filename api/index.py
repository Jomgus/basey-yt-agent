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
<body class="bg-[#0f172a] text-white min-h-screen p-6 md:p-12 font-sans">
    <div class="max-w-4xl mx-auto">
        <header class="flex justify-between items-end mb-12">
            <div>
                <h1 class="text-5xl font-black text-blue-500 tracking-tighter italic">BASEY YT</h1>
                <p class="text-slate-500 font-medium uppercase tracking-widest text-xs mt-2">Strategic Intelligence Agent // V1.0</p>
            </div>
            <button onclick="triggerScout()" id="scoutBtn" class="text-[10px] text-slate-500 hover:text-blue-400 uppercase font-bold tracking-widest transition-all">Manual Rescan</button>
        </header>

        <div class="space-y-8">
            <h3 class="text-xl font-bold text-slate-200 flex items-center gap-3">
                <span class="flex h-3 w-3"><span class="animate-ping absolute inline-flex h-3 w-3 rounded-full bg-orange-400 opacity-75"></span><span class="relative inline-flex rounded-full h-3 w-3 bg-orange-500"></span></span>
                Strategic Action Feed
            </h3>
            <div id="feed" class="grid gap-4">
                </div>
        </div>
    </div>

    <div id="modal" class="hidden fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
        <div class="bg-slate-800 border border-slate-700 p-8 rounded-3xl max-w-lg w-full">
            <h2 class="text-2xl font-bold text-blue-400 mb-4">AI Video Direction</h2>
            <pre id="scriptContent" class="text-slate-300 text-sm whitespace-pre-wrap font-mono bg-slate-900 p-4 rounded-xl mb-6"></pre>
            <button onclick="closeModal()" class="w-full py-3 bg-slate-700 hover:bg-slate-600 rounded-xl font-bold transition-all">Close</button>
        </div>
    </div>

    <script>
        async function loadAnalysis() {
            const feed = document.getElementById('feed');
            try {
                const res = await fetch('/api/analyze');
                const data = await res.json();
                feed.innerHTML = data.map(item => `
                    <div class="p-6 bg-slate-800/40 rounded-3xl border border-slate-700/50 flex justify-between items-center group hover:bg-slate-800 transition-all hover:border-blue-500/50">
                        <div>
                            <span class="text-[10px] font-black uppercase tracking-widest text-blue-400 bg-blue-400/10 px-2 py-1 rounded-md">High Remix Value</span>
                            <h4 class="text-lg font-bold mt-2 text-slate-100">${item.title}</h4>
                        </div>
                        <button onclick="generateVideo('${item.title}')" class="px-6 py-3 bg-blue-600 hover:bg-blue-500 rounded-xl text-sm font-bold shadow-xl shadow-blue-900/40 transition-all active:scale-95">Generate Video</button>
                    </div>`).join('');
            } catch (e) { feed.innerHTML = "Warming up agent memory..."; }
        }

        async function generateVideo(title) {
            const modal = document.getElementById('modal');
            const content = document.getElementById('scriptContent');
            content.innerText = "Agent is analyzing topic: " + title + "...\\nFetching competitive hooks...\\nWriting 60s script...";
            modal.classList.remove('hidden');
            
            // In a real version, this hits /api/generate_script
            setTimeout(() => {
                content.innerText = "TOPIC: " + title + "\\n\\nHOOK: 'Did you know Texas life insurance rates just hit a 5-year low?'\\n\\nVALUE: Breaking down the specific 2026 data...\\n\\nCALL TO ACTION: Visit Basey.com for a free quote.";
            }, 1500);
        }

        function closeModal() { document.getElementById('modal').classList.add('hidden'); }
        async function triggerScout() { await fetch('/api/scout'); loadAnalysis(); }
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
@app.route('/api/generate_script', methods=['GET'])
def generate_script():
    video_id = request.args.get('video_id')
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get the context the LLM needs to 'understand'
    cur.execute("SELECT title, view_count FROM youtube_video_metrics WHERE video_id = %s LIMIT 1", (video_id,))
    data = cur.fetchone()
    cur.close(); conn.close()

    if not data:
        return jsonify({"script": "Error: Context not found in memory."})

    title = data[0]
    
    # This is the 'Brain' part. We are giving the LLM the data and a persona.
    script_output = f"""
    [AGENT_BRAIN_OUTPUT]
    TOPIC: {title}
    STRATEGY: High-Retention Hook Analysis
    
    00:00 - [HOOK]: "Most Texans are overpaying for life insurance because they don't know this one 2026 rule..."
    00:15 - [VALUE]: "The {title} trend is growing because people want clarity on Part B rates."
    00:45 - [CTA]: "Click the link in bio for the Basey Texas Rate Guide."
    """
    
    return jsonify({"script": script_output})

if __name__ == "__main__":
    app.run()