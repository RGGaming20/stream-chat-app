import threading
import time
import queue
import re
import os

from flask import Flask, render_template, jsonify, request, redirect, url_for, session

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key-123")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")  # Set in Render environment variables

# --- TEAM CONFIGURATION ---
TEAMS = {
    "Team SouL":       {"keywords": ["Nakul","nakul","Goblin","goblin","LEGIT","legit","Joker","joker","Thunder","thunder","SOUL","soul","🚀",":rocket:"], "color":"#00fe00","count":0},
    "Genesis Esports": {"keywords": ["GravityJOD","gravityjod","ViPER","viper","HunterZ","hunterz","FurY","fury","Zap","Genesis","genesis"], "color":"#fe6201","count":0},
    "Orangutan":       {"keywords": ["Aaru","aaru","AKOP","akop","Wizz","wizz","Attanki","attanki","OG","og","Orangutan","orangutan","🦧",":orangutan:"], "color":"#de8036","count":0},
    "Victores Sumus":  {"keywords": ["Owais","owais","VeNoM","venom","ScaryJod","scaryjod","Mafia","mafia","Paritosh","paritosh","VS","Victores","victores"], "color":"#fb0600","count":0},
    "GodLike":         {"keywords": ["Manya","manya","ADMINO","admino","Saumay","saumay","Spower","spower","Godz","godz","GodL","godl","GodLike","godlike","💛",":yellow_heart:"], "color":"#e9b346","count":0},
    "RNTX":            {"keywords": ["NinjaJOD","ninjajod","Proton","proton","Sukuna","sukuna","Pain","pain","Tracegod","tracegod","RNTX","rntx","💜","🐺","⚡️","⚡",":purple_heart:",":wolf:",":zap:",":high_voltage:"], "color":"#9903e3","count":0},
    "Wyld Fangs":      {"keywords": ["SENSEI","sensei","SPRAYGOD","spraygod","Goten","goten","Sam","Kanha","kanha","WF","wf","kiwi","Kiwi","Wyld Fangs","wyld fangs","🥝",":kiwi_fruit:"], "color":"#FF0000","count":0},
    "Vasista Esports": {"keywords": ["Hector","hector","Beast","beast","A1mbot","a1mbot","Rony","rony","Dionysus","dionysus","Vasista","vasista"], "color":"#f7f7f7","count":0},
    "Nebula Esports":  {"keywords": ["Aadi","aadi","KnowMe","knowme","Phoenix","phoenix","KRATOS","kratos","Arjun","arjun","Nebula","nebula"], "color":"#9903e3","count":0},
    "Meta Ninza":      {"keywords": ["Fierce","fierce","Apollo","apollo","Auxin","auxin","Javin","javin","Meta","meta","Ninza","ninza"], "color":"#fff539","count":0},
    "Team Tamilas":    {"keywords": ["Tamilas","tamilas","MrIGL","mrigl","Reaper","reaper","AIMGOD","aimgod","Justy","justy","Manty","manty"], "color":"#ffffff","count":0},
    "Welt Esports":    {"keywords": ["Gokul","gokul","Welt","welt","Shyam","shyam","Rico","rico","Dragon","dragon","Poko","poko"], "color":"#00d0ee","count":0},
    "K9 Esports":      {"keywords": ["k9","K9","SnowJOD","snowjod","Taurus","taurus","Smoker","smoker","Stranger","stranger","Saumraj","saumraj","💙",":blue_heart:"], "color":"#0f5088","count":0},
    "Madkings":        {"keywords": ["ClutchGod","clutchgod","SIMP","simp","Troye","troye","Nobi","nobi","MadKings","madkings"], "color":"#419c59","count":0},
    "Apex Gaming":     {"keywords": ["Jelly","jelly","JONATHAN","JONNY","jonny","jonathan","Kio","kio","Hydro","hydro","Harsh","harsh","Apex","apex","🖤","🔝",":black_heart:",":top:"], "color":"#c66e28","count":0},
    "8Bit":            {"keywords": ["8Bit","8bit","Sarang","sarang","Skipz","skipz","Shubh","shubh","Shorty","shorty","Juicy","juicy"], "color":"#f36545","count":0},
    "WindGod":         {"keywords": ["Windgod","windgod","Infinity","infinity","Kyzer","kyzer","Probot","probot","RIOO","rioo","Ryzen","ryzen"], "color":"#fe6f07","count":0},
    "NoNx Esports":    {"keywords": ["Nonx","nonx","Aman","aman","Syrus","syrus","Stunner","stunner","Hexy","hexy","DGbot","dgbot"], "color":"#6b0102","count":0},
    "GENxFM":          {"keywords": ["GENxFM","genxfm","dipop","damu","ghost","buNnY","bunny","moGLi","mogli"], "color":"#f8c858","count":0},
    "Team Aryan":      {"keywords": ["Devotee","devotee","Syrax","syrax","Raiden","raiden","Aryan","aryan","AX"], "color":"#f8c858","count":0},
    "Gods Reign":      {"keywords": ["Neyo","neyo","Justin","justin","DeltaPG","deltapg","AquaNox","aquanox","Destro","destro","GDR","gdr","GodsReign","godsreign","🐉","🔱","🐲",":dragon:",":trident_emblem:",":dragon_face:"], "color":"#dea24e","count":0},
    "True Rippers":    {"keywords": ["Punk","punk","Omega","omega","Termi","termi","Shayaan","shayaan","Achuk","achuk","True Rippers","true rippers"], "color":"#e20000","count":0},
    "Quantum Sparks":  {"keywords": ["MasTer","master","Archit","archit","Yashu","yashu","Daksh","daksh","Scout","scout","Quantum Sparks","quantum sparks","QS","qs","Sparks","sparks","⚡️","⚡",":zap:",":high_voltage:"], "color":"#252525","count":0},
}

# ── Global state ──────────────────────────────────────────────────────────────
chat_queue        = queue.Queue(maxsize=50)
chat_rate_history = []
current_chat_rate = 0
is_connected      = False
error_message     = ""
stream_title      = "No stream connected yet"
total_messages    = 0
chatter_counts    = {}
video_id          = None
should_stop       = False
reconnect_attempts = 0
_bg_thread        = None

# --- ONE VOTE PER USER ---
# Maps username -> team name they voted for (locked for the stream)
user_votes        = {}


# ── YouTube API helpers ───────────────────────────────────────────────────────

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
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            stream_title = resp.json().get("title", vid_id)
            return
    except Exception:
        pass
    stream_title = f"Video: {vid_id}"


def get_live_chat_id(vid_id):
    """Use YouTube Data API to get the liveChatId for a video."""
    try:
        url = "https://www.googleapis.com/youtube/v3/videos"
        params = {
            "part": "liveStreamingDetails",
            "id": vid_id,
            "key": YOUTUBE_API_KEY,
        }
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()

        if "error" in data:
            return None, f"API error: {data['error']['message']}"

        items = data.get("items", [])
        if not items:
            return None, "Video not found or not a live stream"

        details = items[0].get("liveStreamingDetails", {})
        chat_id = details.get("activeLiveChatId")

        if not chat_id:
            return None, "No active live chat found. Is the stream currently live?"

        return chat_id, None

    except Exception as e:
        return None, str(e)


def fetch_chat_messages(live_chat_id, page_token=None):
    """Fetch one page of live chat messages from YouTube API."""
    try:
        url = "https://www.googleapis.com/youtube/v3/liveChat/messages"
        params = {
            "liveChatId": live_chat_id,
            "part": "snippet,authorDetails",
            "maxResults": 200,
            "key": YOUTUBE_API_KEY,
        }
        if page_token:
            params["pageToken"] = page_token

        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()

        if "error" in data:
            return None, None, None, f"API error: {data['error']['message']}"

        messages = []
        for item in data.get("items", []):
            snippet = item.get("snippet", {})
            author  = item.get("authorDetails", {})

            msg_type = snippet.get("type", "")
            if msg_type not in ("textMessageEvent", "superChatEvent", "superStickerEvent"):
                continue

            text = snippet.get("displayMessage", "") or snippet.get("textMessageDetails", {}).get("messageText", "")
            name = author.get("displayName", "")
            pfp  = author.get("profileImageUrl", "")

            if text and name:
                messages.append((name, text, pfp))

        next_token = data.get("nextPageToken")
        polling_ms = data.get("pollingIntervalMillis", 5000)

        return messages, next_token, polling_ms, None

    except Exception as e:
        return None, None, 5000, str(e)


# ── Message processing ────────────────────────────────────────────────────────

def detect_team(msg):
    """
    Return the first team whose keyword appears in the message, or None.
    Checks longer/more-specific keywords first to avoid short-keyword false matches.
    """
    # Sort teams so longer keywords are matched first (avoids "OG" swallowing "Orangutan")
    for team_name, team_data in sorted(
        TEAMS.items(),
        key=lambda x: max((len(k) for k in x[1]["keywords"]), default=0),
        reverse=True
    ):
        for kw in team_data["keywords"]:
            if kw in msg:
                return team_name
    return None


def process_message(author, msg, pfp):
    """
    Count general chat activity, then assign at most ONE team vote per user
    for the entire stream session.  Spam from the same user never adds more votes.
    """
    global total_messages
    total_messages += 1

    # Track chatter activity (still counts all messages for leaderboard)
    if author not in chatter_counts:
        chatter_counts[author] = {"count": 0, "pfp": pfp}
    chatter_counts[author]["count"] += 1
    if pfp:
        chatter_counts[author]["pfp"] = pfp

    # Push to live chat queue
    if chat_queue.full():
        try: chat_queue.get_nowait()
        except: pass
    chat_queue.put({"author": author, "message": msg})

    # ── ONE VOTE PER USER LOGIC ──────────────────────────────────────────────
    # If this user has already voted, ignore any team keywords in future messages
    if author in user_votes:
        return

    # First time this user mentions a team keyword → lock their vote
    team = detect_team(msg)
    if team:
        user_votes[author] = team          # lock the user to this team
        TEAMS[team]["count"] += 1          # add exactly 1 fan to the team
    # ────────────────────────────────────────────────────────────────────────


# ── Background worker ─────────────────────────────────────────────────────────

def chat_worker(vid_id):
    global is_connected, error_message, should_stop, reconnect_attempts
    global current_chat_rate, chat_rate_history

    print(f"[Chat] Starting for {vid_id}")

    if not YOUTUBE_API_KEY:
        error_message = "YOUTUBE_API_KEY not set! Add it in Render environment variables."
        is_connected = False
        return

    # Get live chat ID
    live_chat_id, err = get_live_chat_id(vid_id)
    if not live_chat_id:
        error_message = err or "Could not get live chat ID"
        is_connected = False
        print(f"[Chat] Failed: {error_message}")
        return

    print(f"[Chat] Got liveChatId: {live_chat_id[:20]}...")
    is_connected   = True
    error_message  = ""
    reconnect_attempts = 0

    page_token         = None
    message_timestamps = []
    last_rate_time     = time.time()
    seen_ids           = set()   # avoid processing duplicate messages
    first_fetch        = True

    while not should_stop:
        messages, next_token, polling_ms, err = fetch_chat_messages(live_chat_id, page_token)

        if err:
            print(f"[Chat] Error: {err}")
            reconnect_attempts += 1
            error_message = f"Error: {err}"
            if reconnect_attempts >= 10:
                is_connected = False
                break
            time.sleep(5)
            continue

        reconnect_attempts = 0

        # On first fetch skip existing messages (they're old), just get page token
        if first_fetch:
            first_fetch = False
            page_token = next_token
            wait = max((polling_ms or 5000) / 1000, 2)
            time.sleep(wait)
            continue

        for author, msg, pfp in (messages or []):
            msg_key = f"{author}:{msg}"
            if msg_key in seen_ids:
                continue
            seen_ids.add(msg_key)
            # Keep seen_ids from growing forever
            if len(seen_ids) > 2000:
                seen_ids = set(list(seen_ids)[-1000:])

            process_message(author, msg, pfp)
            message_timestamps.append(time.time())

        if next_token:
            page_token = next_token

        # Update rate
        now = time.time()
        message_timestamps = [t for t in message_timestamps if t > now - 1]
        current_chat_rate  = len(message_timestamps)

        if now - last_rate_time >= 1:
            ts = time.strftime("%H:%M:%S")
            if len(chat_rate_history) > 60:
                chat_rate_history.pop(0)
            chat_rate_history.append({"time": ts, "rate": current_chat_rate})
            last_rate_time = now

        wait = max((polling_ms or 5000) / 1000, 2)
        time.sleep(wait)

    is_connected = False
    print("[Chat] Worker stopped")


# ── Stream control ────────────────────────────────────────────────────────────

def start_stream(url):
    global video_id, is_connected, error_message, should_stop
    global total_messages, chatter_counts, reconnect_attempts, _bg_thread
    global user_votes

    # Stop existing worker
    should_stop = True
    time.sleep(1.5)

    # Reset everything (including per-user vote locks)
    for t in TEAMS: TEAMS[t]["count"] = 0
    while not chat_queue.empty():
        try: chat_queue.get_nowait()
        except: pass
    chat_rate_history.clear()
    chatter_counts     = {}
    total_messages     = 0
    reconnect_attempts = 0
    error_message      = "Connecting to YouTube API..."
    is_connected       = False
    should_stop        = False
    user_votes         = {}        # ← clear vote locks for new stream

    vid_id   = extract_video_id(url)
    video_id = vid_id
    get_stream_title(vid_id)

    _bg_thread = threading.Thread(target=chat_worker, args=(vid_id,), daemon=True)
    _bg_thread.start()

    return True, "Stream started! Fetching live chat..."


# ── Flask routes ──────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/admin", methods=["GET", "POST"])
def admin():
    error   = None
    success = None

    if request.method == "POST":
        action = request.form.get("action")

        if action == "login":
            if request.form.get("password", "") == ADMIN_PASSWORD:
                session["admin"] = True
            else:
                error = "Wrong password!"

        elif action == "logout":
            session.pop("admin", None)
            return redirect(url_for("admin"))

        elif action == "start" and session.get("admin"):
            url = request.form.get("url", "").strip()
            if not YOUTUBE_API_KEY:
                error = "❌ YOUTUBE_API_KEY is not set! Add it in Render → Environment Variables."
            elif url:
                ok, msg = start_stream(url)
                success = f"✅ {msg}"
            else:
                error = "Please paste a YouTube URL"

        elif action == "stop" and session.get("admin"):
            global should_stop, is_connected
            should_stop  = True
            is_connected = False
            success = "⏹️ Stream stopped"

        elif action == "reset_votes" and session.get("admin"):
            global user_votes
            for t in TEAMS: TEAMS[t]["count"] = 0
            user_votes = {}        # ← also clear vote locks on manual reset
            success = "🔄 All fan counts reset to 0"

        elif action == "reset_fans" and session.get("admin"):
            global chatter_counts
            chatter_counts = {}
            success = "🔄 Fan leaderboard reset"

    return render_template("admin.html",
                           logged_in=session.get("admin", False),
                           error=error, success=success,
                           is_connected=is_connected,
                           stream_title=stream_title,
                           video_id=video_id,
                           api_key_set=bool(YOUTUBE_API_KEY))


@app.route("/data")
def get_data():
    sorted_teams = sorted(TEAMS.items(), key=lambda x: x[1]["count"], reverse=True)
    top_8   = sorted_teams[:8]
    layout  = [3, 4, 2, 5, 1, 6, 0, 7]
    podium  = [None] * 8
    for rank, (name, data) in enumerate(top_8):
        podium[layout[rank]] = {"name": name, "count": data["count"], "color": data["color"], "rank": rank + 1}
    for i in range(8):
        if podium[i] is None:
            podium[i] = {"name": "-", "count": 0, "color": "#222222", "rank": "-"}

    top_chatters = sorted(chatter_counts.items(), key=lambda x: x[1]["count"], reverse=True)[:5]
    all_teams    = [{"name": n, "count": d["count"], "color": d["color"], "rank": r + 1}
                    for r, (n, d) in enumerate(sorted_teams)]

    return jsonify({
        "podium":            podium,
        "all_teams":         all_teams,
        "chat_history":      list(chat_queue.queue),
        "rate_current":      current_chat_rate,
        "rate_graph":        chat_rate_history,
        "status":            is_connected,
        "error":             error_message,
        "total":             total_messages,
        "stream_title":      stream_title,
        "reconnect_attempts": reconnect_attempts,
        "top_chatters":      [{"name": n, "count": d["count"], "pfp": d["pfp"]} for n, d in top_chatters],
    })


@app.route("/inject_votes", methods=["POST"])
def inject_votes():
    """Manually add fan counts (bypasses per-user lock — admin use only)."""
    try:
        data = request.get_json()
        if not data or "votes" not in data:
            return jsonify({"success": False, "error": "No votes data"}), 400
        results = []
        for team, count in data["votes"].items():
            if team in TEAMS:
                TEAMS[team]["count"] += count
                results.append({"team": team, "added": count})
            else:
                results.append({"team": team, "error": "Not found"})
        return jsonify({"success": True, "results": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/reset_votes", methods=["POST"])
def reset_votes():
    global user_votes
    for t in TEAMS: TEAMS[t]["count"] = 0
    user_votes = {}
    return jsonify({"success": True})


@app.route("/get_teams")
def get_teams():
    return jsonify({"success": True, "teams": {n: d["count"] for n, d in TEAMS.items()}})


@app.route("/inject_fan", methods=["POST"])
def inject_fan():
    global chatter_counts
    try:
        data  = request.get_json()
        name  = data.get("name", "").strip()
        count = int(data.get("count", 0))
        if not name:
            return jsonify({"success": False, "error": "No username"}), 400
        if name not in chatter_counts:
            chatter_counts[name] = {"count": 0, "pfp": ""}
        chatter_counts[name]["count"] += count
        return jsonify({"success": True, "name": name, "new_total": chatter_counts[name]["count"]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/reset_fans", methods=["POST"])
def reset_fans():
    global chatter_counts
    chatter_counts = {}
    return jsonify({"success": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, port=port, host="0.0.0.0")
