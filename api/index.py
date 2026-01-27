import os
import psycopg2
from flask import Flask, request, jsonify, render_template_string
from googleapiclient.discovery import build
from groq import Groq # Add this to requirements.txt

app = Flask(__name__)

# Credentials
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
client = Groq(api_key=os.getenv("GROQ_API_KEY")) # Add GROQ_API_KEY to Vercel

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Basey YT | Strategy</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background-color: #1a1a1b; color: #d7dadc; font-size: 14px; }
        .card-bg { background-color: #272729; border: 1px solid #343536; }
        .btn-white { background-color: #f1f1f1; color: #0f0f0f; }
    </style>
</head>
<body class="p-4 md:p-8">
    <div class="max-w-4xl mx-auto">
        
        <header class="mb-6 flex justify-between items-end">
            <div>
                <h1 class="text-2xl font-black text-white italic tracking-tighter uppercase">Basey YT</h1>
                <p class="text-[9px] text-gray-500 font-bold uppercase tracking-widest">Strategic Analyst Agent</p>
            </div>
            <div class="text-[9px] text-emerald-500 font-mono">SYSTEM_READY</div>
        </header>

        <div class="card-bg rounded-2xl p-4 mb-6 flex items-center justify-between gap-4">
            <div class="text-xs text-gray-400">
                <span class="font-bold text-gray-200">Passive Discovery:</span> Scanning Texas insurance trends.
            </div>
            <button onclick="triggerScout()" id="scoutBtn" class="bg-white/10 hover:bg-white/20 px-4 py-2 rounded-lg text-[10px] font-bold uppercase tracking-widest transition-all">Manual Rescan</button>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-3 mb-8">
            <button onclick="openChat('Draft a script for ')" class="card-bg p-4 rounded-xl text-left hover:border-gray-500 transition-all">
                <p class="text-[9px] font-bold text-red-500 uppercase mb-1">Production</p>
                <h4 class="text-xs font-bold leading-tight">Draft Counter-Script</h4>
            </button>
            <button onclick="openChat('Analyze this competitor: ')" class="card-bg p-4 rounded-xl text-left hover:border-gray-500 transition-all">
                <p class="text-[9px] font-bold text-red-500 uppercase mb-1">Strategy</p>
                <h4 class="text-xs font-bold leading-tight">Competitor Analysis</h4>
            </button>
            <button onclick="openChat('Give me 5 hooks for ')" class="card-bg p-4 rounded-xl text-left hover:border-gray-500 transition-all">
                <p class="text-[9px] font-bold text-red-500 uppercase mb-1">Creative</p>
                <h4 class="text-xs font-bold leading-tight">Viral Hook Ideas</h4>
            </button>
        </div>

        <div class="space-y-3">
            <p class="text-[9px] font-bold text-gray-600 uppercase tracking-widest mb-2">High-Velocity Targets</p>
            <div id="feed" class="grid gap-2"></div>
        </div>
    </div>

    <div id="chatModal" class="hidden fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
        <div class="card-bg w-full max-w-lg rounded-2xl overflow-hidden flex flex-col shadow-2xl">
            <div class="p-4 border-b border-white/5 flex justify-between items-center bg-white/5">
                <h3 class="font-bold text-sm uppercase tracking-widest">Agent Intelligence</h3>
                <button onclick="closeChat()" class="text-gray-500 hover:text-white">✕</button>
            </div>
            <div id="chatHistory" class="p-4 h-64 overflow-y-auto space-y-4 text-xs">
                <div class="bg-white/5 p-3 rounded-lg text-gray-300">How can I help you dominate this trend today, Tom?</div>
            </div>
            <div id="genActionContainer" class="p-4 hidden border-t border-white/5">
                <button onclick="finalGenerate()" class="w-full py-3 btn-white rounded-xl font-black text-xs uppercase tracking-widest">🚀 Generate Final Video</button>
            </div>
            <div class="p-4 bg-black/20 flex gap-2">
                <input id="chatInput" type="text" class="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-red-500" placeholder="Ask the agent...">
                <button onclick="sendMessage()" class="bg-red-600 px-4 py-2 rounded-lg text-[10px] font-bold uppercase">Send</button>
            </div>
        </div>
    </div>

    <script>
        let currentTarget = "";
        
        async function loadAnalysis() {
            const feed = document.getElementById('feed');
            const res = await fetch('/api/analyze');
            const data = await res.json();
            currentTarget = data[0].title;
            feed.innerHTML = data.map(item => `
                <div class="card-bg p-4 rounded-xl flex justify-between items-center group">
                    <div>
                        <span class="text-[8px] font-black uppercase tracking-widest text-red-500">${item.rec}</span>
                        <h4 class="text-xs font-bold text-gray-200">${item.title}</h4>
                    </div>
                    <button onclick="openChat('Video generation for: ${item.title}')" class="px-4 py-2 btn-white rounded-lg text-[10px] font-black uppercase transition-all active:scale-95">Generate</button>
                </div>`).join('');
        }

        function openChat(msg) {
            document.getElementById('chatModal').classList.remove('hidden');
            if(msg) {
                document.getElementById('chatInput').value = msg;
                sendMessage();
            }
        }

        function closeChat() { document.getElementById('chatModal').classList.add('hidden'); }

        async function sendMessage() {
            const input = document.getElementById('chatInput');
            const history = document.getElementById('chatHistory');
            const genContainer = document.getElementById('genActionContainer');
            
            if(!input.value) return;

            history.innerHTML += `<div class="text-right"><span class="bg-blue-600/20 p-2 rounded-lg inline-block">${input.value}</span></div>`;
            const userMsg = input.value;
            input.value = "";

            // Mock LLM Response for demo
            setTimeout(() => {
                history.innerHTML += `<div class="text-left"><span class="bg-white/5 p-2 rounded-lg inline-block italic">Agent is thinking...</span></div>`;
                setTimeout(() => {
                    history.lastChild.innerHTML = `<span class="bg-white/5 p-2 rounded-lg inline-block">I've analyzed that trend. Based on our conversation, I've prepared a 2026-ready hook. Ready to generate?</span>`;
                    genContainer.classList.remove('hidden');
                }, 1000);
            }, 500);
        }

        function finalGenerate() {
            alert("Video Generation Pipeline Started. Tom will receive a notification when the .mp4 is ready.");
            closeChat();
        }

        async function triggerScout() {
            document.getElementById('scoutBtn').innerText = "SCANNING...";
            await fetch('/api/scout');
            loadAnalysis();
            document.getElementById('scoutBtn').innerText = "MANUAL RESCAN";
        }

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