from flask import Flask, jsonify, render_template, request
from scraper import fetch_trending, LANGUAGE_MAP
from datetime import datetime, timedelta
import threading
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

cache = {
    "daily": {"data": None, "updated_at": None},
    "weekly": {"data": None, "updated_at": None},
    "monthly": {"data": None, "updated_at": None},
}

CACHE_TTL = timedelta(hours=2)
cache_lock = threading.Lock()


def is_cache_valid(since):
    entry = cache.get(since)
    if not entry or not entry["data"] or not entry["updated_at"]:
        return False
    return datetime.now() - entry["updated_at"] < CACHE_TTL


def refresh_cache(since="daily", force=False):
    with cache_lock:
        if not force and is_cache_valid(since):
            return cache[since]["data"]

    logger.info(f"Refreshing cache for '{since}' trending repos...")
    try:
        repos = fetch_trending(since=since)
        with cache_lock:
            cache[since] = {
                "data": repos,
                "updated_at": datetime.now(),
            }
        logger.info(f"Cache refreshed for '{since}': {len(repos)} repos")
        return repos
    except Exception as e:
        logger.error(f"Failed to refresh cache for '{since}': {e}")
        with cache_lock:
            if cache[since]["data"]:
                return cache[since]["data"]
        return []


def background_refresh():
    while True:
        time.sleep(3600)
        for since in ["daily", "weekly", "monthly"]:
            try:
                refresh_cache(since, force=False)
            except Exception as e:
                logger.error(f"Background refresh failed for '{since}': {e}")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/trending")
def api_trending():
    since = request.args.get("since", "daily")
    if since not in ("daily", "weekly", "monthly"):
        since = "daily"

    language = request.args.get("language", "")
    force = request.args.get("force", "0") == "1"

    if force:
        repos = refresh_cache(since, force=True)
    else:
        with cache_lock:
            if is_cache_valid(since):
                repos = cache[since]["data"]
            else:
                repos = None

        if repos is None:
            repos = refresh_cache(since)

    if language:
        repos = [r for r in repos if r.get("language", "").lower() == language.lower()]

    updated_at = None
    with cache_lock:
        entry = cache.get(since)
        if entry and entry["updated_at"]:
            updated_at = entry["updated_at"].isoformat()

    return jsonify({
        "repos": repos[:100],
        "count": len(repos[:100]),
        "since": since,
        "updated_at": updated_at,
    })


@app.route("/api/languages")
def api_languages():
    return jsonify({"languages": LANGUAGE_MAP})


@app.route("/api/refresh", methods=["POST"])
def api_refresh():
    since = request.args.get("since", "daily")
    repos = refresh_cache(since, force=True)
    return jsonify({"status": "ok", "count": len(repos)})


def init_app():
    for since in ["daily", "weekly", "monthly"]:
        refresh_cache(since)

    t = threading.Thread(target=background_refresh, daemon=True)
    t.start()


if __name__ == "__main__":
    init_app()
    app.run(debug=True, host="0.0.0.0", port=5000)