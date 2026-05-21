import threading
import time
import queue
import asyncio
from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import sys
import re
import os

try:
    import pytchat
    PYTCHAT_AVAILABLE = True
except ImportError:
    PYTCHAT_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key-123")

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

# --- TEAM CONFIGURATION ---
TEAMS = {
    "Team SouL": {"keywords": ["Nakul","nakul","Goblin","goblin","LEGIT","legit","Joker","joker","Thunder","thunder","SOUL","soul","🚀",":rocket:"],"color":"#00fe00","count":0},
    "Genesis Esports": {"keywords": ["GravityJOD","gravityjod","ViPER","viper","HunterZ","hunterz","FurY","fury","Zap","Genesis","genesis"],"color":"#fe6201","count":0},
    "Orangutan": {"keywords": ["Aaru","aaru","AKOP","akop","Wizz","wizz","Attanki","attanki","OG","og","Orangutan","orangutan","🦧",":orangutan:"],"color":"#de8036","count":0},
    "Victores Sumus": {"keywords": ["Owais","owais","VeNoM","venom","ScaryJod","scaryjod","Mafia","mafia","Paritosh","paritosh","VS","Victores","victores"],"color":"#fb0600","count":0},
    "GodLike": {"keywords": ["Manya","manya","ADMINO","admino","Saumay","saumay","Spower","spower","Godz","godz","GodL","godl","GodLike","godlike","💛",":yellow_heart:"],"color":"#e9b346","count":0},
    "RNTX": {"keywords": ["NinjaJOD","ninjajod","Proton","proton","Sukuna","sukuna","Pain","pain","Tracegod","tracegod","RNTX","rntx","💜","🐺","⚡️","⚡",":purple_heart:",":wolf:",":zap:",":high_voltage:"],"color":"#9903e3","count":0},
    "Wyld Fangs": {"keywords": ["SENSEI","sensei","SPRAYGOD","spraygod","Goten","goten","Sam","Kanha","kanha","WF","wf","kiwi","Kiwi","Wyld Fangs","wyld fangs","🥝",":kiwi_fruit:"],"color":"#FF0000","count":0},
    "Vasista Esports": {"keywords": ["Hector","hector","Beast","beast","A1mbot","a1mbot","Rony","rony","Dionysus","dionysus","Vasista","vasista"],"color":"#f7f7f7","count":0},
    "Nebula Esports": {"keywords": ["Aadi","aadi","KnowMe","knowme","Phoenix","phoenix","KRATOS","kratos","Arjun","arjun","Nebula","nebula"],"color":"#9903e3","count":0},
    "Meta Ninza": {"keywords": ["Fierce","fierce","Apollo","apollo","Auxin","auxin","Javin","javin","Meta","meta","Ninza","ninza"],"color":"#fff539","count":0},
    "Team Tamilas": {"keywords": ["Tamilas","tamilas","MrIGL","mrigl","Reaper","reaper","AIMGOD","aimgod","Justy","justy","Manty","manty"],"color":"#ffffff","count":0},
    "Welt Esports": {"keywords": ["Gokul","gokul","Welt","welt","Shyam","shyam","Rico","rico","Dragon","dragon","Poko","poko"],"color":"#00d0ee","count":0},
    "K9 Esports": {"keywords": ["k9","K9","SnowJOD","snowjod","Taurus","taurus","Smoker","smoker","Stranger","stranger","Saumraj","saumraj","💙",":blue_heart:"],"color":"#0f5088","count":0},
    "Madkings": {"keywords": ["ClutchGod","clutchgod","SIMP","simp","Troye","troye","Nobi","nobi","MadKings","madkings"],"color":"#419c59","count":0},
    "Apex Gaming": {"keywords": ["Jelly","jelly","JONATHAN","JONNY","jonny","jonathan","Kio","kio","Hydro","hydro","Harsh","harsh","Apex","apex","🖤","🔝",":black_heart:",":top:"],"color":"#c66e28","count":0},
    "8Bit": {"keywords": ["8Bit","8bit","Sarang","sarang","Skipz","skipz","Shubh","shubh","Shorty","shorty","Juicy","juicy"],"color":"#f36545","count":0},
    "WindGod": {"keywords": ["Windgod","windgod","Infinity","infinity","Kyzer","kyzer","Probot","probot","RIOO","rioo","Ryzen","ryzen"],"color":"#fe6f07","count":0},
    "NoNx Esports": {"keywords": ["Nonx","nonx","Aman","aman","Syrus","syrus","Stunner","stunner","Hexy","hexy","DGbot","dgbot"],"color":"#6b0102","count":0},
    "GENxFM": {"keywords": ["GENxFM","genxfm","dipop","damu","ghost","buNnY","bunny","moGLi","mogli"],"color":"#f8c858","count":0},
    "Team Aryan": {"keywords": ["Devotee","devotee","Syrax","syrax","Raiden","raiden","Aryan","aryan","AX"],"color":"#f8c858","count":0},
    "Gods Reign": {"keywords": ["Neyo","neyo","Justin","justin","DeltaPG","deltapg","AquaNox","aquanox","Destro","destro","GDR","gdr","GodsReign","godsreign","🐉","🔱","🐲",":dragon:",":trident_emblem:",":dragon_face:"],"color":"#dea24e","count":0},
    "True Rippers": {"keywords": ["Punk","punk","Omega","omega","Termi","termi","Shayaan","shayaan","Achuk","achuk","True Rippers","true rippers"],"color":"#e20000","count":0},
    "Quantum Sparks": {"keywords": ["MasTer","master","Archit","archit","Yashu","yashu","Daksh","daksh","Scout","scout","Quantum Sparks","quantum sparks","QS","qs","Sparks","sparks","⚡️","⚡",":zap:",":high_voltage:"],"color":"#252525","count":0},
}

# Global state
chat_queue = queue.Queue(maxsize=50)
chat_rate_history = []
current_chat_rate = 0
is_connected = False
error_message = ""
stream_title = "No stream connected yet"
total_messages = 0
chatter_counts = {}
video_id = None
should_stop = False
reconnect_attempts = 0
max_reconnect_attempts = 5
_bg_thread = None


def extract_video_id(url):
    vid_id = url.strip().replace(" ", "")
    if "youtube.com/watch?v=" in vid_id:
        vid_id = vid_id.split("watch?v=")[1].split("&")[0]
    elif "youtu.be/" in vid_id:
        vid_id = vid_id.split("youtu.be/")[1].split("?")[0]
    elif "youtube.com/live/" in vid_id:
        vid_id = vid_id.split("youtube.com/live/")[1].split("?")[0]
    return vid_id.split("?")[0].split("&")[0]


def get_stream_title(vid_id):
    global stream_title
    if not REQUESTS_AVAILABLE:
        stream_title = f"Video ID: {vid_id}"
        return
    try:
        url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid_id}&format=json"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            stream_title = resp.json().get('title', f'Video ID: {vid_id}')
        else:
            stream_title = f"Video ID: {vid_id}"
    except Exception:
        stream_title = f"Video ID: {vid_id}"


def process_message(msg, author, author_pfp):
    """Process one chat message — update counts, queue, etc."""
    global current_chat_rate, total_messages

    total_messages += 1

    if author not in chatter_counts:
        chatter_counts[author] = {"count": 0, "pfp": author_pfp}
    chatter_counts[author]["count"] += 1
    if author_pfp:
        chatter_counts[author]["pfp"] = author_pfp

    if chat_queue.full():
        try:
            chat_queue.get_nowait()
        except:
            pass
    chat_queue.put({"author": author, "message": msg})

    for team_name, team_data in TEAMS.items():
        matches = sum(msg.count(kw) for kw in team_data['keywords'] if kw in msg)
        if matches > 0:
            TEAMS[team_name]['count'] += matches


# ── Async chat loop (runs in its own thread with its own event loop) ──────────

async def _async_chat_loop(vid_id):
    """Async loop using LiveChatAsync — no signal issues."""
    global is_connected, error_message, should_stop, reconnect_attempts
    global current_chat_rate, chat_rate_history

    message_timestamps = []
    last_rate_update = time.time()

    while not should_stop:
        try:
            chat = pytchat.LiveChatAsync(vid_id)
        except Exception as e:
            error_message = f"Could not connect: {e}"
            is_connected = False
            await asyncio.sleep(5)
            reconnect_attempts += 1
            if reconnect_attempts >= max_reconnect_attempts:
                error_message = "Max reconnection attempts reached"
                break
            continue

        if not chat.is_alive():
            error_message = "Stream not live or chat disabled"
            is_connected = False
            await asyncio.sleep(5)
            reconnect_attempts += 1
            if reconnect_attempts >= max_reconnect_attempts:
                break
            continue

        is_connected = True
        error_message = ""
        reconnect_attempts = 0

        async for live_chat in chat.get():
            if should_stop:
                break
            for c in live_chat.items:
                pfp = c.author.imageUrl if hasattr(c.author, 'imageUrl') else ""
                process_message(c.message, c.author.name, pfp)
                message_timestamps.append(time.time())

            # Keep 1-second window for rate
            now = time.time()
            message_timestamps = [t for t in message_timestamps if t > now - 1]
            current_chat_rate = len(message_timestamps)

            # Rate history (every second)
            if now - last_rate_update >= 1:
                ts = time.strftime("%H:%M:%S")
                if len(chat_rate_history) > 60:
                    chat_rate_history.pop(0)
                chat_rate_history.append({"time": ts, "rate": current_chat_rate})
                last_rate_update = now

            await asyncio.sleep(0)  # yield to event loop

        if should_stop:
            break

        # Chat ended — try reconnecting
        is_connected = False
        reconnect_attempts += 1
        if reconnect_attempts >= max_reconnect_attempts:
            error_message = "Max reconnection attempts reached"
            break
        error_message = f"Reconnecting... ({reconnect_attempts}/{max_reconnect_attempts})"
        await asyncio.sleep(5)

    is_connected = False


def _run_async_loop(vid_id):
    """Runs the async chat loop in a dedicated thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_async_chat_loop(vid_id))
    finally:
        loop.close()


def start_stream(url):
    global video_id, is_connected, error_message, should_stop
    global total_messages, chatter_counts, reconnect_attempts, _bg_thread

    # Stop any existing stream
    should_stop = True
    time.sleep(1.5)

    # Reset state
    for t in TEAMS:
        TEAMS[t]['count'] = 0
    while not chat_queue.empty():
        try: chat_queue.get_nowait()
        except: pass
    chat_rate_history.clear()
    chatter_counts = {}
    total_messages = 0
    reconnect_attempts = 0
    error_message = ""
    should_stop = False

    vid_id = extract_video_id(url)
    video_id = vid_id
    get_stream_title(vid_id)

    if not PYTCHAT_AVAILABLE:
        error_message = "pytchat not installed"
        is_connected = False
        return False, "pytchat not installed on server"

    # Launch background thread with its own event loop
    _bg_thread = threading.Thread(target=_run_async_loop, args=(vid_id,), daemon=True)
    _bg_thread.start()

    # Wait briefly to see if connection succeeds
    time.sleep(3)

    if error_message and "not live" in error_message.lower():
        return False, error_message

    return True, "Stream started! Connecting to chat..."


# ── Flask routes ──────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    error = None
    success = None

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'login':
            if request.form.get('password', '') == ADMIN_PASSWORD:
                session['admin'] = True
            else:
                error = "Wrong password!"

        elif action == 'logout':
            session.pop('admin', None)
            return redirect(url_for('admin'))

        elif action == 'start' and session.get('admin'):
            url = request.form.get('url', '').strip()
            if url:
                ok, msg = start_stream(url)
                success = f"✅ {msg}" if ok else None
                error = f"❌ {msg}" if not ok else None
            else:
                error = "Please paste a YouTube URL"

        elif action == 'stop' and session.get('admin'):
            global should_stop, is_connected
            should_stop = True
            is_connected = False
            success = "⏹️ Stream stopped"

        elif action == 'reset_votes' and session.get('admin'):
            for t in TEAMS: TEAMS[t]['count'] = 0
            success = "🔄 All votes reset to 0"

        elif action == 'reset_fans' and session.get('admin'):
            global chatter_counts
            chatter_counts = {}
            success = "🔄 Fan leaderboard reset"

    return render_template('admin.html',
                           logged_in=session.get('admin', False),
                           error=error, success=success,
                           is_connected=is_connected,
                           stream_title=stream_title,
                           video_id=video_id)


@app.route('/data')
def get_data():
    sorted_teams = sorted(TEAMS.items(), key=lambda x: x[1]['count'], reverse=True)
    top_8 = sorted_teams[:8]
    layout = [3, 4, 2, 5, 1, 6, 0, 7]
    podium = [None] * 8
    for rank, (name, data) in enumerate(top_8):
        podium[layout[rank]] = {"name": name, "count": data['count'], "color": data['color'], "rank": rank + 1}
    for i in range(8):
        if podium[i] is None:
            podium[i] = {"name": "-", "count": 0, "color": "#222222", "rank": "-"}

    top_chatters = sorted(chatter_counts.items(), key=lambda x: x[1]['count'], reverse=True)[:5]
    all_teams = [{"name": n, "count": d['count'], "color": d['color'], "rank": r + 1}
                 for r, (n, d) in enumerate(sorted_teams)]

    return jsonify({
        "podium": podium,
        "all_teams": all_teams,
        "chat_history": list(chat_queue.queue),
        "rate_current": current_chat_rate,
        "rate_graph": chat_rate_history,
        "status": is_connected,
        "error": error_message,
        "total": total_messages,
        "stream_title": stream_title,
        "reconnect_attempts": reconnect_attempts,
        "top_chatters": [{"name": n, "count": d["count"], "pfp": d["pfp"]} for n, d in top_chatters]
    })


@app.route('/inject_votes', methods=['POST'])
def inject_votes():
    try:
        data = request.get_json()
        if not data or 'votes' not in data:
            return jsonify({"success": False, "error": "No votes data"}), 400
        results = []
        for team, count in data['votes'].items():
            if team in TEAMS:
                TEAMS[team]['count'] += count
                results.append({"team": team, "added": count})
            else:
                results.append({"team": team, "error": "Not found"})
        return jsonify({"success": True, "results": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/reset_votes', methods=['POST'])
def reset_votes():
    for t in TEAMS: TEAMS[t]['count'] = 0
    return jsonify({"success": True})


@app.route('/get_teams')
def get_teams():
    return jsonify({"success": True, "teams": {n: d['count'] for n, d in TEAMS.items()}})


@app.route('/inject_fan', methods=['POST'])
def inject_fan():
    global chatter_counts
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        count = int(data.get('count', 0))
        if not name:
            return jsonify({"success": False, "error": "No username"}), 400
        if name not in chatter_counts:
            chatter_counts[name] = {"count": 0, "pfp": ""}
        chatter_counts[name]["count"] += count
        return jsonify({"success": True, "name": name, "new_total": chatter_counts[name]["count"]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/reset_fans', methods=['POST'])
def reset_fans():
    global chatter_counts
    chatter_counts = {}
    return jsonify({"success": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, port=port, host='0.0.0.0')
