import sys
import os
from pathlib import Path
from backend import rag

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

COMPANY_NAME = os.getenv("COMPANY_NAME")

def verify_rag():
    # Setup paths
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    knowledge_file = data_dir / "knowledge.json"
    persist_dir = project_root / "chroma_db_test"
    
    # Initialize
    print("Initializing RAG Engine...")
    try:
        from backend.rag import RAGEngine
        rag_engine = RAGEngine(knowledge_file, persist_dir)
        rag_engine.initialize()
    except Exception as e:
        print(f"Initialization failed: {e}")
        return

    print("RAG Initialized.")
    
    # Test
    query = f"What services does {COMPANY_NAME} provide?"
    print(f"\nTesting Search Query: '{query}'")
    
    result = rag_engine.answer_query(query)
    
    print("\nResponse:")
    print(result["response"])
    print("\nSources:")
    for source in result["sources"]:
        print(f"- {source}")

if __name__ == "__main__":
    verify_rag()
