import requests
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

BASE_URL = "https://www.occamsadvisory.com/"
OUTPUT_FILE = "scraper/urls.txt"
USER_AGENT = "Mozilla/5.0 (compatible; AssignmentBot/1.0.0)"
HEADERS = {
    "User-Agent": USER_AGENT
}

def is_relevant_url(url: str) -> bool:
    """
    Filter URLs based on relevance to the company knowledge base.
    
    Rules:
    1. Must be internal.
    2. Must not be a file (pdf/jpg).
    3. Must not be utility pages (login/cart/privacy).
    4. Prioritize content pages (services, blogs, about).
    """
    if not url: return False
    
    parsed = urlparse(url)
    lower_path = parsed.path.lower()
    
    # 1. Domain Check
    domain = parsed.netloc.replace("www.", "")
    base_domain = urlparse(BASE_URL).netloc.replace("www.", "")
    if domain != base_domain:
        return False

    # 2. File Extension Check
    ignored_exts = [".pdf", ".jpg", ".jpeg", ".png", ".gif", ".css", ".js", ".zip", ".xml", ".txt",".php"]
    if any(lower_path.endswith(ext) for ext in ignored_exts):
        return False
        
    # 3. Utility/Noise Page Check (The "Smart Filter")
    ignored_keywords = [
        "/login", "/signin", "/register", "/signup","/index",
        "/cart", "/checkout", "/basket",
        "/my-account", "/account",
        "/privacy-policy", "/terms-of-service", "/terms-conditions", "/legal", "/terms-&",
        "/sitemap", # The sitemap page itself isn't content
        "/tag/", "/category/", "/author/", # Archive pages often duplicate content
        "/page/", # Paginated lists
        "/digital-marketing-agency",
        "/digital-marketing-agency/", # SEO doorway pages (repetitive city/state content)
        "javascript:", "mailto:", "tel:",
        "/artoflivingwcf", "/art-of-living-wcf"
    ]
    
    if any(keyword in lower_path for keyword in ignored_keywords):
        return False
    
    # 4. Optional: Enforce positive relevance?
    # No, because unique pages like "/our-impact" might be missed. 
    # Better to allow everything not explicitly blocked, but prioritize "clean" URLs.
    
    return True

def fetch_sitemap_urls():
    """Fetch and parse sitemap.xml"""
    sitemap_url = BASE_URL.rstrip("/") + "/sitemap.xml"
    print(f"Reading Sitemap: {sitemap_url}")
    
    try:
        resp = requests.get(sitemap_url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            print(f"   Failed to fetch sitemap (Status: {resp.status_code})")
            return []
            
        # Parse XML
        root = ET.fromstring(resp.content)
        
        # Handle default namespace (often present in sitemaps)
        # We'll just search for 'loc' anywhere to be robust
        urls = [elem.text for elem in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
        
        if not urls:
             # Fallback: Search without namespace
            urls = [elem.text for elem in root.findall(".//loc")]
            
        print(f"   Found {len(urls)} candidates in sitemap")
        return urls
        
    except Exception as e:
        print(f"   Error processing sitemap: {e}")
        return []

def main():
    # 1. Fetch Candidates
    candidates = fetch_sitemap_urls()
    
    if not candidates:
        print("No URLs found in sitemap. Please check the URL manually.")
        return
    
    # 2. Filter Relevance
    relevant_urls = set()
    for url in candidates:
        if url:
            # Normalize: Remove trailing slash to avoid duplicates (e.g. /contact/ vs /contact)
            clean_url = url.strip().rstrip("/")
            
            if is_relevant_url(clean_url):
                relevant_urls.add(clean_url)
            
    # 3. Save
    final_list = sorted(list(relevant_urls))
    
    # Ensure homepage is there
    home = BASE_URL.rstrip("/")
    if home not in final_list:
        final_list.insert(0, home)

    print(f"\nFiltered down to {len(final_list)} RELEVANT URLs:")
    with open(OUTPUT_FILE, "w") as f:
        for url in final_list:
            print(f"  - {url}")
            f.write(url + "\n")
            
    print(f"\nSaved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

# Run this script as:
# python -m scraper.discover