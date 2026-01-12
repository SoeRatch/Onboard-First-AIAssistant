import re
from datetime import datetime
from bs4 import BeautifulSoup
from scraper.utils import can_fetch

USER_AGENT = "Mozilla/5.0 (compatible; AssignmentBot/1.0.0)"

class WebContentExtractor:
    def __init__(self, cache_manager):
        self.cache_manager = cache_manager
        self.headers = {
            "User-Agent": USER_AGENT
        }

    def fetch_html(self, url):
        """Fetch HTML content from a URL."""
        import requests
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def extract_text(self, html):
        """Extract clean text and title from HTML."""
        soup = BeautifulSoup(html, "html.parser")

        # Remove specific noisy classes found in inspection
        noisy_classes = [
            "mega-content", "dropdown", "dropdown-ser", "mobile-menu", 
            "sticky-footer", "login_menu", "navi", "top-bar", "footer",
            "search-box", "modal", "breadcrumb", "site-header", "site-footer",
            "nav-menu", "widget", "sidebar", "banner"
        ]
        for cls in noisy_classes:
            for element in soup.find_all(class_=re.compile(cls, re.I)):
                element.decompose()

        for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside", "form", "button", "iframe", "svg"]):
            tag.decompose()

        # Convert <br> and <hr> to line breaks
        for br in soup.find_all(["br", "hr"]):
            br.replace_with("\n")
        
        # Treat lists properly
        for li in soup.find_all("li"):
            # Ensure bullets have newlines
            li.insert_before("\n• ")
        
        for inline_tag in soup.find_all(["strong", "b", "em", "i", "span", "u"]):
            inline_tag.unwrap()

        title = soup.title.get_text().strip() if soup.title else "No Title"
        texts = []
        
        # Extract text blocks
        for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "p", "li"]):
            text = tag.get_text(separator=" ", strip=True)
            # Normalize whitespace
            text = re.sub(r'\s+', ' ', text)
            
            # Filter noise
            noise_patterns = [
                r'^•\s*•\s*•$', # symbolic separators
                r'^(Login|Contact|Career|Blog|Awards|Newsletter|Search|Home|Back to top|Menu)$', # lone navigation words
                r'^Follow Us$', 
                r'^Privacy Policy$',
                r'^\d+\s*reviews?$',
                r'^as seen on$',
                r'^recognised by'
            ]
            
            if any(re.match(p, text, re.IGNORECASE) for p in noise_patterns):
                continue

            # Restore bullet points for valid content
            text = re.sub(r'(?<!\n)•', '\n•', text)
            
            if len(text) > 2:
                texts.append(text)

        # Merge headers with content by joining with newlines
        full_text = "\n".join(texts)
        
        return title, full_text

    def process_url(self, url):
        """Fetch and extract content, returning a structured page dict."""
        print(f"Fetching: {url}")

        cached_html = self.cache_manager.load_from_cache(url)
        if cached_html:
            html = cached_html
        else:
            if not can_fetch(url):
                print(f"[SKIP] Disallowed by robots.txt: {url}")
                return None
            html = self.fetch_html(url)
            if html:
                self.cache_manager.save_to_cache(url, html)

        if not html:
            return None
            
        title, content = self.extract_text(html)
        
        if not content:
            print(f"[SKIP] No relevant content for {url}")
            return None

        # Return dict consistent with what knowledge builder expects
        return {
            "url": url,
            "title": title,
            "scraped_at": datetime.now().isoformat(),
            "main_content": content
        }