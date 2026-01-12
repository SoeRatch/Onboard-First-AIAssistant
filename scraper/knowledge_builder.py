import os
from datetime import datetime
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv
load_dotenv()
COMPANY_NAME = os.getenv("COMPANY_NAME")

SIMILARITY_THRESHOLD = 0.6 # similarity threshold for semantic chunking
MAX_CHARS = 1500  # hard limit
MIN_CHUNK_CHARS = 250 # Ensure chunks have context

embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def categorize_page(url: str) -> str:
    """Determine category based on URL."""
    url_lower = url.lower()
    
    # Core Corporate
    if "/about" in url_lower or "/our-team" in url_lower: return "about"
    if "/contact" in url_lower: return "contact"
    if "/career" in url_lower: return "careers"
    if "/award" in url_lower: return "awards"
    if "/testimonials" in url_lower: return "social_proof"
    
    # Knowledge / Resources
    if "/blog" in url_lower: return "blog"
    if "/faq" in url_lower or "questions" in url_lower or "/faq-" in url_lower: return "faq"
    if "/insights" in url_lower: return "insights"
    if "/related-employee-retention" in url_lower: return "services/erc" # Specific ERC FAQs
    
    # Services
    if "/tax" in url_lower or "/research" in url_lower or "/employee-retention" in url_lower: return "services/tax-credits"
    if "/business" in url_lower or "/incubation" in url_lower: return "services/bsgi"
    if "/technology" in url_lower or "/payment" in url_lower or "/fintech" in url_lower: return "services/ftps"
    if "/capital" in url_lower or "/investment" in url_lower or "/ma" in url_lower: return "services/cmib"
    
    # Homepage
    path = url_lower.rstrip("/").split("/")[-1]
    if path in ["", "www.occamsadvisory.com", "index", "home"]:
        return "homepage"
        
    return "other"


def create_knowledge_chunks(page: dict, start_id: int) -> tuple[list[dict], int]:
    """Create semantic chunks for RAG."""
    content = page.get("main_content", "").strip()
    if not content:
        return [], start_id

    sentences = [s.strip() for s in content.split("\n") if s.strip()]
    if not sentences:
        return [], start_id

    page_url = page["url"]
    page_title = page["title"]
    page_category = categorize_page(page["url"])

    embeddings = embedding_model.encode(sentences)

    chunks = []
    current_chunk = [sentences[0]]
    current_chars = len(sentences[0])
    chunk_id = start_id

    for i in range(1, len(sentences)):
        sim = cosine_similarity([embeddings[i-1]], [embeddings[i]])[0][0]
    
        # Check semantic similarity and hard size limit
        # Merge if similar OR too small to stand alone
        if current_chars < MIN_CHUNK_CHARS or (sim >= SIMILARITY_THRESHOLD and current_chars + len(sentences[i]) < MAX_CHARS):
            current_chunk.append(sentences[i])
            current_chars += len(sentences[i])
        else:
            chunks.append({
                "id": f"chunk_{chunk_id}",
                "source_url": page_url,
                "category": page_category,
                "title": page_title,
                "content": " ".join(current_chunk),
                "metadata": {"type": "semantic"}
            })
            chunk_id += 1
            current_chunk = [sentences[i]]
            current_chars = len(sentences[i])
    
    # Add any remaining chunk
    if current_chunk:
        chunks.append({
            "id": f"chunk_{chunk_id}",
            "source_url": page_url,
            "category": page_category,
            "title": page_title,
            "content": " ".join(current_chunk),
            "metadata": {"type": "semantic"}
        })
        chunk_id += 1

    return chunks, chunk_id

def build_knowledge_base(pages: list[dict]) -> dict:
    all_chunks = []
    next_id = 0
    for page in pages:
        chunks, next_id = create_knowledge_chunks(page, next_id)
        all_chunks.extend(chunks)
    homepage = next((p for p in pages if categorize_page(p["url"]) == "homepage"), None)
    
    return {
        "company": {
            "name": COMPANY_NAME,
            "website": homepage["url"] if homepage else "",
            "description": homepage["main_content"][:500] if homepage else ""
        },
        "pages": pages, # Keep raw pages too
        "chunks": all_chunks, # The RAG-ready chunks
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_pages": len(pages),
            "total_chunks": len(all_chunks)
        }
    }