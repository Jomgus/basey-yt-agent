import os
import psycopg2
from flask import Flask, request, jsonify, render_template_string
from googleapiclient.discovery import build

app = Flask(__name__)

# Credentials
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

# --- THE EXECUTIVE INTERFACE ---
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Basey YT | Strategy Hub</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background-color: #1a1a1b; color: #d7dadc; font-size: 15px; }
        .card-bg { background-color: #272729; border: 1px solid #343536; }
        .btn-white { background-color: #f1f1f1; color: #0f0f0f; }
        .chat-bubble-agent { background-color: #343536; border: 1px solid #444; }
        .chat-bubble-user { background-color: #dc2626; color: white; }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-thumb { background: #444; border-radius: 10px; }
    </style>
</head>
<body class="p-6 md:p-12">
    <div class="max-w-5xl mx-auto">
        
        <header class="mb-8 flex justify-between items-end">
            <div>
                <h1 class="text-3xl font-black text-white italic tracking-tighter uppercase">Basey YT</h1>
                <p class="text-xs text-gray-500 font-bold uppercase tracking-[0.2em] mt-1">Strategic Analyst Agent // V1.0</p>
            </div>
            <div class="text-xs text-emerald-500 font-mono flex items-center gap-2">
                <span class="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></span>
                SYSTEM_LIVE
            </div>
        </header>

        <div class="card-bg rounded-2xl p-6 mb-8 flex items-center justify-between gap-6 shadow-xl">
            <div class="text-sm text-gray-400">
                <span class="font-bold text-gray-100">Passive Discovery Engine:</span> Active & Scanning Texas niche.
            </div>
            <button onclick="triggerScout()" id="scoutBtn" class="bg-white/10 hover:bg-white/20 px-6 py-3 rounded-xl text-xs font-bold uppercase tracking-widest transition-all">Manual Rescan</button>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-10">
            <button onclick="openChat('Draft a counter-script for the current top trend.')" class="card-bg p-6 rounded-3xl text-left hover:border-gray-400 transition-all group">
                <p class="text-[10px] font-black text-red-600 uppercase mb-2 group-hover:text-red-500">Production</p>
                <h4 class="text-sm font-bold leading-tight text-gray-200">Draft Counter-Script</h4>
            </button>
            <button onclick="openChat('Why are competitors winning in the Texas market right now?')" class="card-bg p-6 rounded-3xl text-left hover:border-gray-400 transition-all group">
                <p class="text-[10px] font-black text-red-600 uppercase mb-2 group-hover:text-red-500">Strategy</p>
                <h4 class="text-sm font-bold leading-tight text-gray-200">Competitor Analysis</h4>
            </button>
            <button onclick="openChat('Give me 5 viral hooks for insurance shorts.')" class="card-bg p-6 rounded-3xl text-left hover:border-gray-400 transition-all group">
                <p class="text-[10px] font-black text-red-600 uppercase mb-2 group-hover:text-red-500">Creative</p>
                <h4 class="text-sm font-bold leading-tight text-gray-200">Viral Hook Ideas</h4>
            </button>
        </div>

        <div class="space-y-4">
            <p class="text-xs font-black text-gray-600 uppercase tracking-[0.3em] mb-4 px-1">Strategic Action Feed</p>
            <div id="feed" class="grid gap-3">
                </div>
        </div>
    </div>

    <div id="chatModal" class="hidden fixed inset-0 bg-black/70 backdrop-blur-md flex items-center justify-center p-4 z-50">
        <div class="card-bg w-full max-w-xl rounded-[32px] overflow-hidden flex flex-col shadow-2xl h-[600px] border-[#444]">
            <div class="p-5 border-b border-white/5 flex justify-between items-center bg-white/5">
                <div>
                    <h3 class="font-bold text-xs uppercase tracking-widest text-white">Agent Intelligence</h3>
                    <p class="text-[9px] text-gray-500 font-mono">ENCRYPTED_LINK_ESTABLISHED</p>
                </div>
                <button onclick="closeChat()" class="text-gray-500 hover:text-white text-xl">✕</button>
            </div>
            <div id="chatHistory" class="p-6 flex-1 overflow-y-auto space-y-5">
                <div class="chat-bubble-agent p-4 rounded-2xl text-gray-300 max-w-[85%] text-sm">
                    Analysis complete. I've mapped the top 3 trends in your niche. How shall we proceed with the video generation, Tom?
                </div>
            </div>
            <div id="genActionContainer" class="p-6 hidden border-t border-white/5 bg-white/5">
                <button onclick="finalGenerate()" class="w-full py-5 btn-white rounded-2xl font-black text-xs uppercase tracking-widest shadow-2xl hover:bg-white transition-all">🚀 Generate Final Video</button>
            </div>
            <div class="p-5 bg-black/30 flex gap-3">
                <input id="chatInput" type="text" onkeypress="handleKey(event)" class="flex-1 bg-white/5 border border-white/10 rounded-2xl px-5 py-4 text-sm focus:outline-none focus:border-red-600 transition-all" placeholder="Message the agent...">
                <button onclick="sendMessage()" class="bg-red-600 px-6 py-4 rounded-2xl text-xs font-bold uppercase hover:bg-red-500 transition-all text-white">Send</button>
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
                    <div class="card-bg p-6 rounded-2xl flex justify-between items-center group hover:bg-[#2e2e30] transition-all">
                        <div>
                            <span class="text-[9px] font-black uppercase tracking-widest text-red-600">${item.rec}</span>
                            <h4 class="text-base font-bold text-gray-100 mt-1">${item.title}</h4>
                        </div>
                        <button onclick="openChat('Generate strategy for: ${item.title}')" class="px-6 py-3 btn-white rounded-xl text-xs font-black uppercase transition-all active:scale-95 shadow-md">Generate</button>
                    </div>`).join('');
            } catch (e) { feed.innerHTML = "<div class='p-6 text-center text-gray-600 font-mono'>ESTABLISHING NEON_LINK...</div>"; }
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
            history.innerHTML += `<div class="flex justify-end"><span class="chat-bubble-user p-4 rounded-2xl shadow-lg">${userMsg}</span></div>`;
            input.value = "";
            history.scrollTop = history.scrollHeight;

            const loadingId = "loading-" + Date.now();
            history.innerHTML += `<div id="${loadingId}" class="flex justify-start"><span class="chat-bubble-agent p-4 rounded-2xl italic text-gray-500 animate-pulse">Analyst is calculating...</span></div>`;
            
            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ message: userMsg })
                });
                const data = await res.json();
                document.getElementById(loadingId).remove();
                history.innerHTML += `<div class="flex justify-start"><span class="chat-bubble-agent p-4 rounded-2xl text-gray-200">${data.reply}</span></div>`;
                
                if (data.reply.includes("READY_TO_GENERATE")) {
                    genContainer.classList.remove('hidden');
                }
            } catch (err) {
                document.getElementById(loadingId).innerHTML = "<span class='text-red-500'>Link unstable. Check Vercel logs.</span>";
            }
            history.scrollTop = history.scrollHeight;
        }

        function finalGenerate() {
            alert("Video Rendering Logic Initiated. Tom will receive an email with the download link.");
            closeChat();
        }

        async function triggerScout() {
            const btn = document.getElementById('scoutBtn');
            btn.innerText = "SCOUTING...";
            await fetch('/api/scout');
            loadAnalysis();
            btn.innerText = "COMPLETE";
            setTimeout(() => btn.innerText = "MANUAL RESCAN", 3000);
        }

        loadAnalysis();
    </script>
</body>
</html>
"""

# --- THE BACKEND LOGIC ---

@app.route('/')
def home():
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
    except Exception:
        return jsonify({"reply": "System Error: Missing AI library."})

    user_msg = request.json.get("message")
    try:
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You are the Basey YT Strategic Analyst. You are talking to Tom. Be brief, authoritative, and helpful. If he agrees to a video idea, you MUST include the phrase READY_TO_GENERATE in your reply."},
                {"role": "user", "content": user_msg}
            ]
        )
        return jsonify({"reply": completion.choices[0].message.content})
    except Exception as e:
        return jsonify({"reply": f"Brain offline: {str(e)}"})

@app.route('/api/scout', methods=['GET'])
def run_scout():
    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY, cache_discovery=False)
        request_yt = youtube.search().list(q="Texas insurance trends", part="snippet", type="video", maxResults=10, order="viewCount")
        res = request_yt.execute()
        conn = get_db_connection(); cur = conn.cursor()
        for item in res.get('items', []):
            cur.execute("INSERT INTO youtube_benchmarks (video_id, title) VALUES (%s, %s) ON CONFLICT (video_id) DO NOTHING;", (item['id']['videoId'], item['snippet']['title']))
        conn.commit(); cur.close(); conn.close()
        return jsonify({"status": "Success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze', methods=['GET'])
def get_analysis():
    try:
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("SELECT title, agent_recommendation FROM v_strategic_benchmarks LIMIT 3")
        rows = cur.fetchall()
        analysis = [{"title": r[0], "rec": r[1]} for r in rows]
        cur.close(); conn.close()
        return jsonify(analysis)
    except Exception:
        return jsonify([])

if __name__ == "__main__":
    app.run()