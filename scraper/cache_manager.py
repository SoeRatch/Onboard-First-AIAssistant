from pathlib import Path
from typing import Optional
import hashlib
import time

class CacheManager:
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)

    def get_cache_path(self, url: str) -> Path:
        """Generate cache file path for a URL."""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return self.cache_dir / f"{url_hash}.html"

    def load_from_cache(self, url: str) -> Optional[str]:
        """Load cached HTML content if available and fresh (< 72 hours)."""
        cache_path = self.get_cache_path(url)
        if cache_path.exists():
            # Check if cache is fresh (less than  hours old)
            age_hours = (time.time() - cache_path.stat().st_mtime) / 3600
            if age_hours < 72:
                print(f"Using cached content for {url}")
                return cache_path.read_text(encoding="utf-8")
        return None
    
    def save_to_cache(self, url: str, html: str):
        """Save HTML content to cache."""
        cache_path = self.get_cache_path(url)
        cache_path.write_text(html, encoding="utf-8") #here write_text is a method of Path class that writes text to a file