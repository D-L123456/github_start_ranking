import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GITHUB_TRENDING_URL = "https://github.com/trending"

LANGUAGE_MAP = {
    "": "All",
    "python": "Python",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "java": "Java",
    "go": "Go",
    "rust": "Rust",
    "c++": "C++",
    "c": "C",
    "c#": "C#",
    "ruby": "Ruby",
    "php": "PHP",
    "swift": "Swift",
    "kotlin": "Kotlin",
    "scala": "Scala",
    "shell": "Shell",
    "dart": "Dart",
    "html": "HTML",
    "css": "CSS",
}


def fetch_trending(since="daily", language="", spoken_language=""):
    params = {"since": since}
    if language:
        params["l"] = language
    if spoken_language:
        params["spoken_language_code"] = spoken_language

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    try:
        response = requests.get(GITHUB_TRENDING_URL, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        return _parse_trending_page(response.text, since)
    except requests.RequestException as e:
        logger.error(f"Failed to fetch trending repos: {e}")
        return []


def _parse_trending_page(html, since="daily"):
    soup = BeautifulSoup(html, "lxml")
    articles = soup.select("article.Box-row")
    repos = []

    for idx, article in enumerate(articles, 1):
        try:
            repo = _parse_repo_article(article, idx, since)
            if repo:
                repos.append(repo)
        except Exception as e:
            logger.warning(f"Failed to parse repo at index {idx}: {e}")
            continue

    return repos


def _parse_repo_article(article, rank, since):
    h2_tag = article.select_one("h2 a")
    if not h2_tag:
        return None

    href = h2_tag.get("href", "").strip("/")
    parts = href.split("/")
    if len(parts) < 2:
        return None
    owner, name = parts[0], parts[1]

    desc_tag = article.select_one("p.col-9")
    description = desc_tag.get_text(strip=True) if desc_tag else ""

    lang_tag = article.select_one("[itemprop='programmingLanguage']")
    language = lang_tag.get_text(strip=True) if lang_tag else ""

    stars_tag = article.select_one("a.Link[href$='/stargazers']")
    total_stars = _parse_number(stars_tag.get_text(strip=True)) if stars_tag else 0

    forks_tag = article.select_one("a.Link[href$='/forks']")
    total_forks = _parse_number(forks_tag.get_text(strip=True)) if forks_tag else 0

    today_stars = 0
    today_tag = article.select_one("span.d-inline-block.float-sm-right")
    if today_tag:
        today_stars = _parse_number(today_tag.get_text(strip=True))
    else:
        for span in article.select("span.d-inline-block"):
            text = span.get_text(strip=True).lower()
            if "star" in text:
                today_stars = _parse_number(text)
                break

    built_by = []
    for img in article.select("a[data-hovercard-type='user'] img"):
        alt = img.get("alt", "").strip("@")
        if alt:
            built_by.append(alt)

    since_label = {"daily": "today", "weekly": "this week", "monthly": "this month"}.get(since, "today")

    return {
        "rank": rank,
        "owner": owner,
        "name": name,
        "full_name": f"{owner}/{name}",
        "url": f"https://github.com/{owner}/{name}",
        "description": description,
        "language": language,
        "total_stars": total_stars,
        "total_forks": total_forks,
        "stars_since": today_stars,
        "since_label": since_label,
        "built_by": built_by[:5],
    }


def _parse_number(text):
    import re
    text = text.replace(",", "")
    match = re.search(r"([\d.]+)\s*k?", text, re.IGNORECASE)
    if not match:
        return 0
    try:
        num_str = match.group(1)
        if "k" in text[match.start():].lower():
            return int(float(num_str) * 1000)
        return int(float(num_str))
    except (ValueError, TypeError):
        return 0


if __name__ == "__main__":
    repos = fetch_trending(since="daily")
    for r in repos[:10]:
        print(f"#{r['rank']} {r['full_name']} ⭐{r['total_stars']} (+{r['stars_since']} today) [{r['language']}]")