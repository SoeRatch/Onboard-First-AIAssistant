import sys
import random
import time

from pathlib import Path
import json
from scraper.cache_manager import CacheManager
from scraper.utils import setup_directories, load_urls
from scraper.content_extractor import WebContentExtractor
from scraper.knowledge_builder import build_knowledge_base

RATE_LIMIT_DELAY_RANGE = (1.5, 2.5)  # Delay between requests in seconds

# Paths
SCRIPT_DIR = Path(__file__).parent # directory that contains the current script.
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
URLS_FILE = SCRIPT_DIR / "urls.txt"
OUTPUT_FILE = DATA_DIR / "knowledge.json"
CACHE_DIR = DATA_DIR / "cache"


# ---------- Main ----------
if __name__ == "__main__":

    # 1. Setup
    setup_directories(DATA_DIR, CACHE_DIR)
    urls = load_urls(URLS_FILE)

    if not urls:
        print("No URLs found in urls.txt. Run discover.py first")
        sys.exit(1)

    print(f"\nFound {len(urls)} URLs to scrape")

    # 2. Initialize Components
    cache_manager = CacheManager(CACHE_DIR)
    extractor = WebContentExtractor(cache_manager)
    
    scraped_pages = []

    # 3. Scrape Loop
    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] Processing URL: {url}")
        page_data = extractor.process_url(url)
        if page_data:
            scraped_pages.append(page_data)
        
        if i < len(urls):
            time.sleep(random.uniform(*RATE_LIMIT_DELAY_RANGE))

    # 4. Build Knowledge Base
    print("Building structured knowledge base...")
    kb = build_knowledge_base(scraped_pages)

    # 5. Save Output
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(kb, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved Knowledge Base to {OUTPUT_FILE}")
    print(f"   - Total Pages: {kb['metadata']['total_pages']}")
    print(f"   - Total Chunks: {kb['metadata']['total_chunks']}")
    print("=" * 60)

# Run it like this - 
# python -m scraper.scrape