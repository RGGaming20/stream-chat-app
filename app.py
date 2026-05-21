import threading
import time
import queue
from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import sys
import re
import os

# Try to import pytchat and handle if not installed
try:
    import pytchat
    PYTCHAT_AVAILABLE = True
except ImportError:
    PYTCHAT_AVAILABLE = False

# Try to import requests for fetching video info
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key-123")

# --- ADMIN PASSWORD (set via environment variable on Render) ---
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

# --- TEAM CONFIGURATION ---
TEAMS = {
    "Team SouL": {
        "keywords": ["Nakul", "nakul", "Goblin", "goblin", "LEGIT", "legit", "Joker", "joker", "Thunder", "thunder", "SOUL", "soul", "🚀", ":rocket:"],
        "color": "#00fe00",
        "count": 0
    },
    "Genesis Esports": {
        "keywords": ["GravityJOD", "gravityjod", "ViPER", "viper", "HunterZ", "hunterz", "FurY", "fury", "Zap", "Genesis", "genesis"],
        "color": "#fe6201",
        "count": 0
    },
    "Orangutan": {
        "keywords": ["Aaru", "aaru", "AKOP", "akop", "Wizz", "wizz", "Attanki", "attanki", "OG", "og", "Orangutan", "orangutan", "🦧", ":orangutan:"],
        "color": "#de8036",
        "count": 0
    },
    "Victores Sumus": {
        "keywords": ["Owais", "owais", "VeNoM", "venom", "ScaryJod", "scaryjod", "Mafia", "mafia", "Paritosh", "paritosh", "VS", "Victores", "victores"],
        "color": "#fb0600",
        "count": 0
    },
    "GodLike": {
        "keywords": ["Manya", "manya", "ADMINO", "admino", "Saumay", "saumay", "Spower", "spower", "Godz", "godz", "GodL", "godl", "GodLike", "godlike", "💛", ":yellow_heart:"],
        "color": "#e9b346",
        "count": 0
    },
    "RNTX": {
        "keywords": ["NinjaJOD", "ninjajod", "Proton", "proton", "Sukuna", "sukuna", "Pain", "pain", "Tracegod", "tracegod", "RNTX", "rntx", "💜", "🐺", "⚡️", "⚡", ":purple_heart:", ":wolf:", ":zap:", ":high_voltage:"],
        "color": "#9903e3",
        "count": 0
    },
    "Wyld Fangs": {
        "keywords": ["SENSEI", "sensei", "SPRAYGOD", "spraygod", "Goten", "goten", "Sam", "Kanha", "kanha", "WF", "wf", "kiwi", "Kiwi", "Wyld Fangs", "wyld fangs", "🥝", ":kiwi_fruit:"],
        "color": "#FF0000",
        "count": 0
    },
    "Vasista Esports": {
        "keywords": ["Hector", "hector", "Beast", "beast", "A1mbot", "a1mbot", "Rony", "rony", "Dionysus", "dionysus", "Vasista", "vasista"],
        "color": "#f7f7f7",
        "count": 0
    },
    "Nebula Esports": {
        "keywords": ["Aadi", "aadi", "KnowMe", "knowme", "Phoenix", "phoenix", "KRATOS", "kratos", "Arjun", "arjun", "Nebula", "nebula"],
        "color": "#9903e3",
        "count": 0
    },
    "Meta Ninza": {
        "keywords": ["Fierce", "fierce", "Apollo", "apollo", "Auxin", "auxin", "Javin", "javin", "Meta", "meta", "Ninza", "ninza"],
        "color": "#fff539",
        "count": 0
    },
    "Team Tamilas": {
        "keywords": ["Tamilas", "tamilas", "MrIGL", "mrigl", "Reaper", "reaper", "AIMGOD", "aimgod", "Justy", "justy", "Manty", "manty"],
        "color": "#ffffff",
        "count": 0
    },
    "Welt Esports": {
        "keywords": ["Gokul", "gokul", "Welt", "welt", "Shyam", "shyam", "Rico", "rico", "Dragon", "dragon", "Poko", "poko"],
        "color": "#00d0ee",
        "count": 0
    },
    "K9 Esports": {
        "keywords": ["k9", "K9", "SnowJOD", "snowjod", "Taurus", "taurus", "Smoker", "smoker", "Stranger", "stranger", "Saumraj", "saumraj", "💙", ":blue_heart:"],
        "color": "#0f5088",
        "count": 0
    },
    "Madkings": {
        "keywords": ["ClutchGod", "clutchgod", "SIMP", "simp", "Troye", "troye", "Nobi", "nobi", "MadKings", "madkings"],
        "color": "#419c59",
        "count": 0
    },
    "Apex Gaming": {
        "keywords": ["Jelly", "jelly", "JONATHAN", "JONNY", "jonny", "jonathan", "Kio", "kio", "Hydro", "hydro", "Harsh", "harsh", "Apex", "apex", "🖤", "🔝", ":black_heart:", ":top:"],
        "color": "#c66e28",
        "count": 0
    },
    "8Bit": {
        "keywords": ["8Bit", "8bit", "Sarang", "sarang", "Skipz", "skipz", "Shubh", "shubh", "Shorty", "shorty", "Juicy", "juicy"],
        "color": "#f36545",
        "count": 0
    },
    "WindGod": {
        "keywords": ["Windgod", "windgod", "Infinity", "infinity", "Kyzer", "kyzer", "Probot", "probot", "RIOO", "rioo", "Ryzen", "ryzen"],
        "color": "#fe6f07",
        "count": 0
    },
    "NoNx Esports": {
        "keywords": ["Nonx", "nonx", "Aman", "aman", "Syrus", "syrus", "Stunner", "stunner", "Hexy", "hexy", "DGbot", "dgbot"],
        "color": "#6b0102",
        "count": 0
    },
    "GENxFM": {
        "keywords": ["GENxFM", "genxfm", "dipop", "damu", "ghost", "buNnY", "bunny", "moGLi", "mogli"],
        "color": "#f8c858",
        "count": 0
    },
    "Team Aryan": {
        "keywords": ["Devotee", "devotee", "Syrax", "syrax", "Raiden", "raiden", "Aryan", "aryan", "AX"],
        "color": "#f8c858",
        "count": 0
    },
    "Gods Reign": {
        "keywords": ["Neyo", "neyo", "Justin", "justin", "DeltaPG", "deltapg", "AquaNox", "aquanox", "Destro", "destro", "GDR", "gdr", "GodsReign", "godsreign", "🐉", "🔱", "🐲", ":dragon:", ":trident_emblem:", ":dragon_face:"],
        "color": "#dea24e",
        "count": 0
    },
    "True Rippers": {
        "keywords": ["Punk", "punk", "Omega", "omega", "Termi", "termi", "Shayaan", "shayaan", "Achuk", "achuk", "True Rippers", "true rippers"],
        "color": "#e20000",
        "count": 0
    },
    "Quantum Sparks": {
        "keywords": ["MasTer", "master", "Archit", "archit", "Yashu", "yashu", "Daksh", "daksh", "Scout", "scout", "Quantum Sparks", "quantum sparks", "QS", "qs", "Sparks", "sparks", "⚡️", "⚡", ":zap:", ":high_voltage:"],
        "color": "#252525",
        "count": 0
    }
}

# Global Variables
chat_queue = queue.Queue(maxsize=50)
chat_rate_history = []
current_chat_rate = 0
is_connected = False
error_message = ""
stream_title = "No stream connected yet"
total_messages = 0
chat_object = None
video_id = None
should_stop = False
reconnect_attempts = 0
max_reconnect_attempts = 5
chatter_counts = {}
chat_thread = None
rate_thread = None


def extract_video_id(url):
    vid_id = url.strip().replace(" ", "")
    if "youtube.com/watch?v=" in vid_id:
        vid_id = vid_id.split("watch?v=")[1].split("&")[0]
    elif "youtu.be/" in vid_id:
        vid_id = vid_id.split("youtu.be/")[1].split("?")[0]
    elif "youtube.com/live/" in vid_id:
        vid_id = vid_id.split("youtube.com/live/")[1].split("?")[0]
    vid_id = vid_id.split("?")[0].split("&")[0]
    return vid_id


def get_stream_title(vid_id):
    global stream_title
    if not REQUESTS_AVAILABLE:
        stream_title = f"Video ID: {vid_id}"
        return
    try:
        url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid_id}&format=json"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            stream_title = data.get('title', f'Video ID: {vid_id}')
        else:
            stream_title = f"Video ID: {vid_id}"
    except Exception:
        stream_title = f"Video ID: {vid_id}"


def reconnect_to_chat():
    global chat_object, is_connected, error_message, reconnect_attempts
    try:
        if chat_object:
            try:
                chat_object.terminate()
            except:
                pass
        time.sleep(3)
        chat_object = pytchat.create(video_id=video_id)
        time.sleep(2)
        if chat_object.is_alive():
            is_connected = True
            error_message = ""
            reconnect_attempts = 0
            return True
        else:
            reconnect_attempts += 1
            error_message = f"Reconnection failed (Attempt {reconnect_attempts}/{max_reconnect_attempts})"
            return False
    except Exception as e:
        reconnect_attempts += 1
        error_message = f"Reconnection error: {str(e)}"
        return False


def chat_processor():
    global current_chat_rate, is_connected, error_message, total_messages, chat_object, should_stop, reconnect_attempts, chatter_counts
    message_timestamps = []
    consecutive_errors = 0
    max_consecutive_errors = 10

    while not should_stop:
        try:
            if not chat_object or not chat_object.is_alive():
                is_connected = False
                if reconnect_attempts < max_reconnect_attempts:
                    if reconnect_to_chat():
                        consecutive_errors = 0
                        continue
                    else:
                        time.sleep(5)
                        continue
                else:
                    error_message = "Connection lost - Max reconnection attempts reached"
                    break

            try:
                data = chat_object.get()
                items = data.sync_items()
                consecutive_errors = 0
            except Exception as e:
                consecutive_errors += 1
                if consecutive_errors >= max_consecutive_errors:
                    is_connected = False
                    if reconnect_attempts < max_reconnect_attempts:
                        if reconnect_to_chat():
                            consecutive_errors = 0
                            continue
                    else:
                        error_message = "Too many errors - Connection unstable"
                        break
                time.sleep(1)
                continue

            if items:
                for c in items:
                    msg = c.message
                    author = c.author.name
                    author_pfp = c.author.imageUrl if hasattr(c.author, 'imageUrl') else ""
                    total_messages += 1

                    if author not in chatter_counts:
                        chatter_counts[author] = {"count": 0, "pfp": author_pfp}
                    chatter_counts[author]["count"] += 1
                    if author_pfp:
                        chatter_counts[author]["pfp"] = author_pfp

                    if chat_queue.full():
                        chat_queue.get()
                    chat_queue.put({"author": author, "message": msg})

                    now = time.time()
                    message_timestamps.append(now)

                    for team_name, team_data in TEAMS.items():
                        matches_found = 0
                        for keyword in team_data['keywords']:
                            if keyword in msg:
                                count = msg.count(keyword)
                                matches_found += count
                        if matches_found > 0:
                            TEAMS[team_name]['count'] += matches_found

            now = time.time()
            message_timestamps = [t for t in message_timestamps if t > now - 1]
            current_chat_rate = len(message_timestamps)
            time.sleep(0.3)

        except Exception as e:
            consecutive_errors += 1
            if consecutive_errors >= max_consecutive_errors:
                is_connected = False
                if reconnect_attempts < max_reconnect_attempts:
                    if reconnect_to_chat():
                        consecutive_errors = 0
                        continue
            time.sleep(1)

    is_connected = False


def rate_monitor():
    global should_stop
    while not should_stop:
        timestamp = time.strftime("%H:%M:%S")
        if len(chat_rate_history) > 60:
            chat_rate_history.pop(0)
        chat_rate_history.append({"time": timestamp, "rate": current_chat_rate})
        time.sleep(1)


def start_stream(url):
    """Start reading a YouTube stream. Called from admin panel."""
    global chat_object, video_id, is_connected, error_message, should_stop
    global total_messages, chatter_counts, chat_thread, rate_thread, reconnect_attempts

    # Stop existing stream if any
    should_stop = True
    time.sleep(1)

    # Reset everything
    for team_name in TEAMS:
        TEAMS[team_name]['count'] = 0
    while not chat_queue.empty():
        try:
            chat_queue.get_nowait()
        except:
            pass
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
        error_message = "pytchat is not installed on the server"
        is_connected = False
        return False, "pytchat not installed"

    try:
        chat_object = pytchat.create(video_id=vid_id)
        time.sleep(2)

        if not chat_object.is_alive():
            error_message = "Stream not live or chat disabled"
            is_connected = False
            return False, "Stream not live or chat is disabled"

        is_connected = True
        error_message = ""

        chat_thread = threading.Thread(target=chat_processor, daemon=True)
        chat_thread.start()

        rate_thread = threading.Thread(target=rate_monitor, daemon=True)
        rate_thread.start()

        return True, "Connected successfully!"

    except Exception as e:
        error_message = str(e)
        is_connected = False
        return False, str(e)


# ─── ROUTES ─────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    """Admin panel — only you can access this with the password."""
    error = None
    success = None

    if request.method == 'POST':
        action = request.form.get('action')

        # Login
        if action == 'login':
            pwd = request.form.get('password', '')
            if pwd == ADMIN_PASSWORD:
                session['admin'] = True
            else:
                error = "Wrong password!"

        # Logout
        elif action == 'logout':
            session.pop('admin', None)
            return redirect(url_for('admin'))

        # Start stream
        elif action == 'start' and session.get('admin'):
            url = request.form.get('url', '').strip()
            if url:
                ok, msg = start_stream(url)
                if ok:
                    success = f"✅ Connected! {msg}"
                else:
                    error = f"❌ Failed: {msg}"
            else:
                error = "Please paste a YouTube URL"

        # Stop stream
        elif action == 'stop' and session.get('admin'):
            global should_stop, is_connected
            should_stop = True
            is_connected = False
            success = "⏹️ Stream stopped"

        # Reset votes
        elif action == 'reset_votes' and session.get('admin'):
            for team_name in TEAMS:
                TEAMS[team_name]['count'] = 0
            success = "🔄 All votes reset to 0"

        # Reset fans
        elif action == 'reset_fans' and session.get('admin'):
            global chatter_counts
            chatter_counts = {}
            success = "🔄 Fan leaderboard reset"

    return render_template('admin.html',
                           logged_in=session.get('admin', False),
                           error=error,
                           success=success,
                           is_connected=is_connected,
                           stream_title=stream_title,
                           video_id=video_id)


@app.route('/data')
def get_data():
    sorted_teams = sorted(TEAMS.items(), key=lambda x: x[1]['count'], reverse=True)
    top_8 = sorted_teams[:8]

    podium = [None] * 8
    layout = [3, 4, 2, 5, 1, 6, 0, 7]

    for rank, (team_name, team_data) in enumerate(top_8):
        if rank < 8:
            pos = layout[rank]
            podium[pos] = {
                "name": team_name,
                "count": team_data['count'],
                "color": team_data['color'],
                "rank": rank + 1
            }

    for i in range(8):
        if podium[i] is None:
            podium[i] = {"name": "-", "count": 0, "color": "#222222", "rank": "-"}

    top_chatters = sorted(chatter_counts.items(), key=lambda x: x[1]['count'], reverse=True)[:5]
    top_chatters_list = [{"name": name, "count": data["count"], "pfp": data["pfp"]} for name, data in top_chatters]

    all_teams_list = [
        {"name": team_name, "count": team_data['count'], "color": team_data['color'], "rank": rank + 1}
        for rank, (team_name, team_data) in enumerate(sorted_teams)
    ]

    return jsonify({
        "podium": podium,
        "all_teams": all_teams_list,
        "chat_history": list(chat_queue.queue),
        "rate_current": current_chat_rate,
        "rate_graph": chat_rate_history,
        "status": is_connected,
        "error": error_message,
        "total": total_messages,
        "stream_title": stream_title,
        "reconnect_attempts": reconnect_attempts,
        "top_chatters": top_chatters_list
    })


@app.route('/inject_votes', methods=['POST'])
def inject_votes():
    try:
        data = request.get_json()
        if not data or 'votes' not in data:
            return jsonify({"success": False, "error": "No votes data provided"}), 400
        votes = data['votes']
        results = []
        for team_name, vote_count in votes.items():
            if team_name in TEAMS:
                TEAMS[team_name]['count'] += vote_count
                results.append({"team": team_name, "added": vote_count})
            else:
                results.append({"team": team_name, "error": "Team not found"})
        return jsonify({"success": True, "results": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/reset_votes', methods=['POST'])
def reset_votes():
    try:
        for team_name in TEAMS:
            TEAMS[team_name]['count'] = 0
        return jsonify({"success": True, "message": "All votes reset"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/get_teams')
def get_teams():
    team_data = {name: data['count'] for name, data in TEAMS.items()}
    return jsonify({"success": True, "teams": team_data})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, port=port, host='0.0.0.0')
