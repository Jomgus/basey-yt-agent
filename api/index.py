import os
import psycopg2
from flask import Flask, request, jsonify, render_template_string
from googleapiclient.discovery import build

# Initialize Flask
app = Flask(__name__)

# Credentials
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

# --- THE STRATEGIC INTERFACE (HTML/CSS/JS) ---
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Basey YT | Strategy Hub</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background-color: #1a1a1b; color: #d7dadc; font-size: 13px; }
        .card-bg { background-color: #272729; border: 1px solid #343536; }
        .btn-white { background-color: #f1f1f1; color: #0f0f0f; }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-thumb { background: #343536; border-radius: 10px; }
    </style>
</head>
<body class="p-4 md:p-8">
    <div class="max-w-4xl mx-auto">
        
        <header class="mb-6 flex justify-between items-end">
            <div>
                <h1 class="text-2xl font-black text-white italic tracking-tighter uppercase">Basey YT</h1>
                <p class="text-[9px] text-gray-500 font-bold uppercase tracking-widest">Strategic Analyst Agent // V1.0</p>
            </div>
            <div class="text-[9px] text-emerald-500 font-mono flex items-center gap-2">
                <span class="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse"></span>
                SYSTEM_READY
            </div>
        </header>

        <div class="card-bg rounded-2xl p-4 mb-6 flex items-center justify-between gap-4">
            <div class="text-xs text-gray-400">
                <span class="font-bold text-gray-200">Passive Discovery:</span> Agent is currently scouting Texas insurance trends.
            </div>
            <button onclick="triggerScout()" id="scoutBtn" class="bg-white/10 hover:bg-white/20 px-4 py-2 rounded-lg text-[9px] font-bold uppercase tracking-widest transition-all">Manual Rescan</button>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-3 mb-8">
            <button onclick="openChat('Draft a counter-script for the current top trend.')" class="card-bg p-5 rounded-2xl text-left hover:border-gray-500 transition-all">
                <p class="text-[9px] font-bold text-red-500 uppercase mb-1">Production</p>
                <h4 class="text-xs font-bold leading-tight">Draft Counter-Script</h4>
            </button>
            <button onclick="openChat('Why are competitors winning in the Texas market right now?')" class="card-bg p-5 rounded-2xl text-left hover:border-gray-500 transition-all">
                <p class="text-[9px] font-bold text-red-500 uppercase mb-1">Strategy</p>
                <h4 class="text-xs font-bold leading-tight">Competitor Analysis</h4>
            </button>
            <button onclick="openChat('Give me 5 viral hooks for insurance shorts.')" class="card-bg p-5 rounded-2xl text-left hover:border-gray-500 transition-all">
                <p class="text-[9px] font-bold text-red-500 uppercase mb-1">Creative</p>
                <h4 class="text-xs font-bold leading-tight">Viral Hook Ideas</h4>
            </button>
        </div>

        <div class="space-y-3">
            <p class="text-[9px] font-bold text-gray-600 uppercase tracking-widest mb-2 px-1">High-Velocity Targets</p>
            <div id="feed" class="grid gap-2">
                </div>
        </div>
    </div>

    <div id="chatModal" class="hidden fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
        <div class="card-bg w-full max-w-lg rounded-2xl overflow-hidden flex flex-col shadow-2xl h-[500px]">
            <div class="p-4 border-b border-white/5 flex justify-between items-center bg-white/5">
                <h3 class="font-bold text-[10px] uppercase tracking-widest">Agent Intelligence</h3>
                <button onclick="closeChat()" class="text-gray-500 hover:text-white">✕</button>
            </div>
            <div id="chatHistory" class="p-6 flex-1 overflow-y-auto space-y-4">
                <div class="bg-white/5 p-3 rounded-xl text-gray-300 max-w-[80%]">How can I help you dominate this trend today, Tom?</div>
            </div>
            <div id="genActionContainer" class="p-4 hidden animate-bounce">
                <button onclick="finalGenerate()" class="w-full py-4 btn-white rounded-xl font-black text-[10px] uppercase tracking-widest shadow-xl">🚀 Generate Video Now</button>
            </div>
            <div class="p-4 bg-black/20 flex gap-2">
                <input id="chatInput" type="text" onkeypress="handleKey(event)" class="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-xs focus:outline-none focus:border-red-600 transition-all" placeholder="Brief the agent...">
                <button onclick="sendMessage()" class="bg-red-600 px-5 py-3 rounded-xl text-[10px] font-bold uppercase hover:bg-red-500 transition-all">Send</button>
            </div>
        </div>
    </div>

    <script>
        async function loadAnalysis() {
            const feed = document.getElementById('feed');
            try {
                const res = await fetch('/api/analyze');
                const data = await res.json();
                feed.innerHTML = data.map(item => `
                    <div class="card-bg p-4 rounded-xl flex justify-between items-center group hover:bg-[#2a2a2a] transition-all">
                        <div>
                            <span class="text-[8px] font-black uppercase tracking-widest text-red-500">${item.rec}</span>
                            <h4 class="text-xs font-bold text-gray-200 mt-0.5">${item.title}</h4>
                        </div>
                        <button onclick="openChat('Generate a video strategy for: ${item.title}')" class="px-4 py-2 btn-white rounded-lg text-[10px] font-black uppercase transition-all active:scale-95">Generate</button>
                    </div>`).join('');
            } catch (e) { feed.innerHTML = "<div class='p-4 text-center text-gray-600'>Priming database link...</div>"; }
        }

        function openChat(msg) {
            document.getElementById('chatModal').classList.remove('hidden');
            if(msg) {
                document.getElementById('chatInput').value = msg;
                sendMessage();
            }
        }

        function closeChat() { 
            document.getElementById('chatModal').classList.add('hidden');
            document.getElementById('genActionContainer').classList.add('hidden');
        }

        function handleKey(e) { if(e.key === 'Enter') sendMessage(); }

        async function sendMessage() {
            const input = document.getElementById('chatInput');
            const history = document.getElementById('chatHistory');
            const genContainer = document.getElementById('genActionContainer');
            if(!input.value) return;

            const userMsg = input.value;
            history.innerHTML += `<div class="flex justify-end"><span class="bg-red-600/10 border border-red-600/20 p-3 rounded-2xl text-gray-200">${userMsg}</span></div>`;
            input.value = "";
            history.scrollTop = history.scrollHeight;

            const loadingId = "loading-" + Date.now();
            history.innerHTML += `<div id="${loadingId}" class="flex justify-start"><span class="bg-white/5 p-3 rounded-2xl italic text-gray-500">Agent is thinking...</span></div>`;
            
            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ message: userMsg })
                });
                const data = await res.json();
                document.getElementById(loadingId).remove();
                history.innerHTML += `<div class="flex justify-start"><span class="bg-white/5 p-3 rounded-2xl text-gray-300 border border-white/5">${data.reply}</span></div>`;
                
                if (data.reply.includes("READY_TO_GENERATE")) {
                    genContainer.classList.remove('hidden');
                }
            } catch (err) {
                document.getElementById(loadingId).innerHTML = "System link unstable.";
            }
            history.scrollTop = history.scrollHeight;
        }

        function finalGenerate() {
            alert("Video Render Pipeline Triggered. Tom will be notified when the .mp4 is ready.");
            closeChat();
        }

        async function triggerScout() {
            const btn = document.getElementById('scoutBtn');
            btn.innerText = "SCANNING...";
            await fetch('/api/scout');
            loadAnalysis();
            btn.innerText = "SCAN COMPLETE";
            setTimeout(() => btn.innerText = "MANUAL RESCAN", 3000);
        }

        loadAnalysis();
    </script>
</body>
</html>
"""

# --- ROUTES ---

@app.route('/')
def home():
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handles the Strategic Chat Intelligence via Groq"""
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
    except ImportError:
        return jsonify({"reply": "AI library missing from deployment environment."})

    user_msg = request.json.get("message")
    try:
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You are the Basey YT Strategic Analyst. You help Tom (an insurance expert) dominate his niche. Be professional and concise. If Tom agrees to a content plan or asks for a video, end your response with exactly: READY_TO_GENERATE."},
                {"role": "user", "content": user_msg}
            ],
            temperature=0.6,
            max_tokens=200
        )
        return jsonify({"reply": completion.choices[0].message.content})
    except Exception as e:
        return jsonify({"reply": f"Analyst Offline: {str(e)}"})

@app.route('/api/scout', methods=['GET'])
def run_scout():
    """Triggers the YouTube Discovery Scout"""
    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY, cache_discovery=False)
        yt_request = youtube.search().list(q="Texas life insurance tips", part="snippet", type="video", maxResults=10, order="viewCount")
        response = yt_request.execute()
        conn = get_db_connection(); cur = conn.cursor()
        for item in response.get('items', []):
            cur.execute("INSERT INTO youtube_benchmarks (video_id, title) VALUES (%s, %s) ON CONFLICT (video_id) DO NOTHING;", (item['id']['videoId'], item['snippet']['title']))
        conn.commit(); cur.close(); conn.close()
        return jsonify({"status": "Success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze', methods=['GET'])
def get_analysis():
    """Pulls the Top 3 targets from Neon SQL"""
    try:
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("SELECT title, agent_recommendation FROM v_strategic_benchmarks LIMIT 3")
        rows = cur.fetchall()
        analysis = [{"title": r[0], "rec": r[1]} for r in rows]
        cur.close(); conn.close()
        return jsonify(analysis)
    except Exception as e:
        return jsonify([])

if __name__ == "__main__":
    app.run()