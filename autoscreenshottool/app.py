import os
import time
import threading
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from PIL import ImageGrab

app = Flask(__name__, static_folder=".")
CORS(app)

# Global state
state = {
    "running": False,
    "current": 0,
    "total": 0,
    "log": [],
    "folder": "screenshots"
}

stop_flag = threading.Event()


# Screenshot function
def run_screenshots(folder, interval, total):
    stop_flag.clear()
    state["running"] = True
    state["current"] = 0
    state["total"] = total
    state["folder"] = folder
    state["log"] = []

    def add_log(msg, kind="info"):
        state["log"].append({"msg": msg, "kind": kind})

    add_log(f"Starting... {total} screenshots every {interval} seconds")

    if not os.path.exists(folder):
        os.makedirs(folder)

    for i in range(1, total + 1):
        if stop_flag.is_set():
            add_log("Stopped by user.", "error")
            break

        filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".png"
        filepath = os.path.join(folder, filename)

        try:
            screenshot = ImageGrab.grab()
            screenshot.save(filepath)
            add_log(f"Saved: {filepath}", "save")
        except Exception as e:
            add_log(f"Error: {e}", "error")

        state["current"] = i

        if i < total and not stop_flag.is_set():
            time.sleep(interval)

    state["running"] = False
    add_log("Finished.", "done")


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/start", methods=["POST"])
def start():
    if state["running"]:
        return jsonify({"error": "Already running"}), 400

    data = request.get_json()

    folder = data.get("folder", "screenshots")
    interval = int(data.get("interval", 2))
    total = int(data.get("total", 10))

    thread = threading.Thread(
        target=run_screenshots,
        args=(folder, interval, total),
        daemon=True
    )
    thread.start()

    return jsonify({"status": "started"})


@app.route("/stop", methods=["POST"])
def stop():
    stop_flag.set()
    return jsonify({"status": "stopping"})


@app.route("/status")
def status():
    return jsonify(state)


if __name__ == "__main__":
    print("Auto Screenshot Tool")
    print("Open: http://127.0.0.1:5000")
    app.run(debug=False, port=5000)