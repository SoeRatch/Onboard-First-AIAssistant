# scraper/utils.py
import re
from urllib.parse import urlparse
import urllib.robotparser
import requests
from urllib.parse import urlparse

REQUEST_TIMEOUT = 10
USER_AGENT = "Mozilla/5.0 (compatible; AssignmentBot/1.0.0)"


def can_fetch(url: str) -> bool:
    """Check if crawling is allowed by robots.txt."""
    parsed = urlparse(url)
    domain = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        headers = {"User-Agent": USER_AGENT}
        res = requests.get(domain, headers=headers, timeout=REQUEST_TIMEOUT)
        if res.status_code >= 400:
            # When you get a 4xx or 5xx error on /robots.txt, it means
            # the site doesn’t have a robots.txt file (404 Not Found), or
            # it is temporarily unavailable (500, 502, 503, etc.).
            # If robots.txt not accessible, assume allowed
            return True
        
        rp = urllib.robotparser.RobotFileParser()
        rp.parse(res.text.splitlines())
        # return rp.can_fetch(USER_AGENT, url)
        return rp.can_fetch("*", url)
    except requests.exceptions.Timeout:
        print(f"[WARN] robots.txt request timed out for {domain}, assuming allowed.")
        return True
    except Exception as e:
        print(f"[WARN] Error checking robots.txt for {domain}: {e}")
        return True

def setup_directories(data_dir, cache_dir):
    """Create necessary directories if they don't exist."""
    data_dir.mkdir(exist_ok=True)
    cache_dir.mkdir(exist_ok=True)

def load_urls(file_path):
    """Load URLs to scrape from a file."""
    urls = []
    if not file_path.exists():
        return urls
        
    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if line and not line.startswith("#"):
                urls.append(line)
    return urls