import threading
import time
import queue
import re
import os
import json

from flask import Flask, render_template, jsonify, request, redirect, url_for, session

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
max_reconnect_attempts = 10
_bg_thread = None

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}


def extract_video_id(url):
    vid = url.strip().replace(" ", "")
    if "youtube.com/watch?v=" in vid:
        vid = vid.split("watch?v=")[1].split("&")[0]
    elif "youtu.be/" in vid:
        vid = vid.split("youtu.be/")[1].split("?")[0]
    elif "youtube.com/live/" in vid:
        vid = vid.split("youtube.com/live/")[1].split("?")[0]
    return vid.split("?")[0].split("&")[0]


def get_stream_title(vid_id):
    global stream_title
    try:
        url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid_id}&format=json"
        resp = requests.get(url, timeout=5, headers=HEADERS)
        if resp.status_code == 200:
            stream_title = resp.json().get('title', f'Video ID: {vid_id}')
            return
    except Exception:
        pass
    stream_title = f"Video ID: {vid_id}"


def get_initial_chat_data(vid_id):
    """Fetch the initial YouTube page to get continuation token and API key."""
    try:
        url = f"https://www.youtube.com/watch?v={vid_id}"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return None, None, None

        html = resp.text

        # Extract API key
        api_key = None
        key_match = re.search(r'"INNERTUBE_API_KEY":"([^"]+)"', html)
        if key_match:
            api_key = key_match.group(1)

        # Extract continuation token for live chat
        cont_match = re.search(r'"continuation":"([^"]+)".*?"Live chat"', html)
        if not cont_match:
            cont_match = re.search(r'"live_chat".*?"continuation":"([^"]+)"', html)
        if not cont_match:
            # Try broader search
            cont_match = re.search(r'continuationData.*?"continuation":"([^"]+)"', html)
        if not cont_match:
            cont_match = re.search(r'"continuation":"([^"]{50,})"', html)

        continuation = cont_match.group(1) if cont_match else None

        # Extract client version
        ver_match = re.search(r'"clientVersion":"([^"]+)"', html)
        client_version = ver_match.group(1) if ver_match else "2.20240101.00.00"

        return api_key, continuation, client_version

    except Exception as e:
        return None, None, None


def fetch_chat_page(api_key, continuation, client_version):
    """Fetch one page of live chat messages."""
    try:
        url = f"https://www.youtube.com/youtubei/v1/live_chat/get_live_chat?key={api_key}"
        payload = {
            "context": {
                "client": {
                    "clientName": "WEB",
                    "clientVersion": client_version,
                    "hl": "en",
                    "gl": "US",
                }
            },
            "continuation": continuation
        }
        resp = requests.post(url, json=payload, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return None, None

        data = resp.json()

        # Extract messages
        messages = []
        try:
            actions = data["continuationContents"]["liveChatContinuation"]["actions"]
            for action in actions:
                try:
                    item = action["addChatItemAction"]["item"]
                    renderer = item.get("liveChatTextMessageRenderer") or item.get("liveChatPaidMessageRenderer")
                    if not renderer:
                        continue
                    author = renderer["authorName"]["simpleText"]
                    pfp = ""
                    if renderer.get("authorPhoto", {}).get("thumbnails"):
                        pfp = renderer["authorPhoto"]["thumbnails"][0]["url"]
                    # Build message text from runs
                    msg_parts = []
                    for run in renderer.get("message", {}).get("runs", []):
                        if "text" in run:
                            msg_parts.append(run["text"])
                        elif "emoji" in run:
                            emoji = run["emoji"]
                            if emoji.get("isCustomEmoji"):
                                msg_parts.append(emoji.get("shortcuts", [""])[0] if emoji.get("shortcuts") else "")
                            else:
                                msg_parts.append(emoji.get("emojiId", ""))
                    msg = "".join(msg_parts)
                    if msg:
                        messages.append((author, msg, pfp))
                except Exception:
                    continue
        except Exception:
            pass

        # Extract next continuation token
        next_cont = None
        try:
            conts = data["continuationContents"]["liveChatContinuation"]["continuations"]
            for c in conts:
                if "invalidationContinuationData" in c:
                    next_cont = c["invalidationContinuationData"]["continuation"]
                    break
                if "timedContinuationData" in c:
                    next_cont = c["timedContinuationData"]["continuation"]
                    break
                if "liveChatReplayContinuationData" in c:
                    next_cont = c["liveChatReplayContinuationData"]["continuation"]
                    break
        except Exception:
            pass

        return messages, next_cont

    except Exception as e:
        return None, None


def process_message(msg, author, pfp):
    global total_messages
    total_messages += 1

    if author not in chatter_counts:
        chatter_counts[author] = {"count": 0, "pfp": pfp}
    chatter_counts[author]["count"] += 1
    if pfp:
        chatter_counts[author]["pfp"] = pfp

    if chat_queue.full():
        try: chat_queue.get_nowait()
        except: pass
    chat_queue.put({"author": author, "message": msg})

    for team_name, team_data in TEAMS.items():
        matches = sum(msg.count(kw) for kw in team_data['keywords'] if kw in msg)
        if matches > 0:
            TEAMS[team_name]['count'] += matches


def chat_worker(vid_id):
    """Main background thread — polls YouTube live chat via HTTP."""
    global is_connected, error_message, should_stop, reconnect_attempts
    global current_chat_rate, chat_rate_history

    message_timestamps = []
    last_rate_time = time.time()

    print(f"[Chat] Starting for video: {vid_id}")

    # Get initial data
    api_key, continuation, client_version = get_initial_chat_data(vid_id)

    if not api_key or not continuation:
        error_message = "Could not connect to live chat. Is the stream live?"
        is_connected = False
        print(f"[Chat] Failed to get initial data. api_key={bool(api_key)}, cont={bool(continuation)}")
        return

    is_connected = True
    error_message = ""
    print(f"[Chat] Connected! api_key={api_key[:10]}...")

    consecutive_failures = 0

    while not should_stop:
        messages, next_cont = fetch_chat_page(api_key, continuation, client_version)

        if messages is None:
            consecutive_failures += 1
            print(f"[Chat] Fetch failed ({consecutive_failures})")
            if consecutive_failures >= 5:
                # Try to re-initialise
                print("[Chat] Re-initialising connection...")
                api_key, continuation, client_version = get_initial_chat_data(vid_id)
                if not api_key or not continuation:
                    reconnect_attempts += 1
                    if reconnect_attempts >= max_reconnect_attempts:
                        error_message = "Lost connection to chat"
                        is_connected = False
                        break
                    error_message = f"Reconnecting... ({reconnect_attempts}/{max_reconnect_attempts})"
                    time.sleep(5)
                    continue
                else:
                    consecutive_failures = 0
                    is_connected = True
                    error_message = ""
            time.sleep(2)
            continue

        consecutive_failures = 0

        for author, msg, pfp in messages:
            process_message(msg, author, pfp)
            message_timestamps.append(time.time())

        if next_cont:
            continuation = next_cont

        # Update rate
        now = time.time()
        message_timestamps = [t for t in message_timestamps if t > now - 1]
        current_chat_rate = len(message_timestamps)

        if now - last_rate_time >= 1:
            ts = time.strftime("%H:%M:%S")
            if len(chat_rate_history) > 60:
                chat_rate_history.pop(0)
            chat_rate_history.append({"time": ts, "rate": current_chat_rate})
            last_rate_time = now

        time.sleep(2)  # Poll every 2 seconds

    is_connected = False
    print("[Chat] Worker stopped")


def start_stream(url):
    global video_id, is_connected, error_message, should_stop
    global total_messages, chatter_counts, reconnect_attempts, _bg_thread

    # Stop existing
    should_stop = True
    time.sleep(1.5)

    # Reset
    for t in TEAMS: TEAMS[t]['count'] = 0
    while not chat_queue.empty():
        try: chat_queue.get_nowait()
        except: pass
    chat_rate_history.clear()
    chatter_counts = {}
    total_messages = 0
    reconnect_attempts = 0
    error_message = "Connecting..."
    is_connected = False
    should_stop = False

    vid_id = extract_video_id(url)
    video_id = vid_id
    get_stream_title(vid_id)

    _bg_thread = threading.Thread(target=chat_worker, args=(vid_id,), daemon=True)
    _bg_thread.start()

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
                success = f"✅ {msg}"
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
