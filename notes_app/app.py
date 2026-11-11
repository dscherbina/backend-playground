import json
import os
import platform
import signal
import sys
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, url_for
from waitress import serve

VERSION = "1.1"
NOTES_FILE = Path(__file__).parent / "data" / "notes.json"

app = Flask(__name__)
app.json.ensure_ascii = False
app.json.sort_keys = False


def load_notes() -> list[str]:
    if not NOTES_FILE.exists():
        return []
    return json.loads(NOTES_FILE.read_text(encoding="utf-8"))


def save_notes(notes: list[str]) -> None:
    NOTES_FILE.parent.mkdir(exist_ok=True)
    NOTES_FILE.write_text(json.dumps(notes, ensure_ascii=False, indent=2), encoding="utf-8")


@app.get("/")
def index() -> str:
    return render_template(
        "index.html",
        title=os.environ.get("APP_TITLE", "Нотатки"),
        author=os.environ.get("AUTHOR", "невідомий"),
        notes=load_notes(),
        version=VERSION,
    )


@app.post("/add")
def add():
    text = request.form.get("text", "").strip()
    if text:
        save_notes([*load_notes(), text])
    return redirect(url_for("index"))


@app.get("/info")
def info():
    return jsonify(
        title=os.environ.get("APP_TITLE", "Нотатки"),
        author=os.environ.get("AUTHOR", "невідомий"),
        version=VERSION,
        notes=len(load_notes()),
        python=platform.python_version(),
    )


def stop(*_) -> None:
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, stop)
    print("Застосунок запущено на порту 8000", flush=True)
    serve(app, host="0.0.0.0", port=8000)
