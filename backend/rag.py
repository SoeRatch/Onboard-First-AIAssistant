import os
from pathlib import Path
import json
# from langchain.schema import Document --- IGNORE --- not working
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.retrievers import BM25Retriever
# from langchain.retrievers import EnsembleRetriever --- IGNORE --- not working
# from langchain_community.retrievers import EnsembleRetriever --- IGNORE --- not working
from langchain_classic.retrievers import EnsembleRetriever
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser 

from dotenv import load_dotenv
load_dotenv()
COMPANY_NAME = os.getenv("COMPANY_NAME")

class RAGEngine:
    def __init__(self, knowledge_file: Path, persist_dir: Path, embedding_model="all-MiniLM-L6-v2"):
        self.knowledge_file = knowledge_file
        self.persist_dir = persist_dir
        self.embedding_model = embedding_model
        self.dense_vectorstore = None
        self.dense_retriever = None
        self.sparse_retriever= None
        self.hybrid_retriever = None
        
        self.embeddings = HuggingFaceEmbeddings(model_name=embedding_model)
        
        # Lightweight LLM for reranking, cheap and appropriate for the task
        self.rerank_llm = ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0
        )
        # Stronger proprietary model for final answering
        self.answer_llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0
            )

    def chunks_to_documents(self, chunks: list[dict]):
        return [
            Document(
                page_content=chunk["content"],
                metadata={
                    "id": chunk["id"],
                    "source_url": chunk["source_url"],
                    "category": chunk["category"],
                    "title": chunk["title"]
                }
            )
            for chunk in chunks
        ]

    def initialize(self):
        """Load knowledge base and initialize ChromaDB."""
        if not self.knowledge_file.exists():
            print("Knowledge file missing at {self.knowledge_file}")
            return

        with open(self.knowledge_file, "r", encoding="utf-8") as f:
            kb = json.load(f)

        chunks = kb.get("chunks", [])
        if not chunks:
            print("No chunks found")
            return

        documents = self.chunks_to_documents(chunks)

        self.dense_vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            collection_name="company_knowledge",
            persist_directory=str(self.persist_dir),
            ids=[doc.metadata["id"] for doc in documents]  # safe restart
        )

        self.dense_retriever = self.dense_vectorstore.as_retriever(search_kwargs={"k": 5})

        # Initialize BM25 (Sparse)
        self.sparse_retriever = BM25Retriever.from_documents(documents, search_kwargs={"k": 10})

        # Hybrid Ensemble
        self.hybrid_retriever = EnsembleRetriever(
            retrievers=[self.dense_retriever, self.sparse_retriever],
            weights=[0.7, 0.3]
        )

        print(f"RAG initialized with {len(documents)} documents")
    
    
    def get_retriever(self, mode="hybrid"):
        if mode == "dense":
            return self.dense_retriever
        elif mode == "sparse":
            return self.sparse_retriever
        else:
            return self.hybrid_retriever

    def get_relevant_documents(self, query: str):
        if not self.hybrid_retriever:
            return []
        retrieved_docs = self.hybrid_retriever.invoke(query)
        return retrieved_docs

    def rerank_documents(self, query: str, retrieved_docs: list[Document]) -> list[Document]:
        """Use LLM to rerank retrieved documents for relevance."""
        if not retrieved_docs:
            return []

        rerank_prompt = PromptTemplate.from_template("""
            You are a ranking assistant. Your job is to re-rank a list of following documents based on how useful and relevant they are for answering the user's question.
                
            ### User Question:
            "{question}"
                
            ### Documents:
            {documents}

            ---

            ### Instructions:
            - Read all documents.
            - Think about the relevance of each document to the user's question.
            - Rank the documents from most relevant to least relevant.     
            - Output the ranking as a comma-separated list of document numbers.    
            - VERY IMPORTANT:
            - Output ONLY the numbers.
            - Do NOT output explanations.
            - Do NOT output any text other than the numbers.

            ### Output format (STRICT):
            1, 3, 2, 4
        """)
        
        chain = rerank_prompt | self.rerank_llm | StrOutputParser()

        doc_lines = [f"{i+1}. {doc.page_content}" for i, doc in enumerate(retrieved_docs)]
        formatted_docs = "\n".join(doc_lines)

        try:
            response = chain.invoke({"question": query, "documents": formatted_docs})
            indices = [int(x.strip()) - 1 for x in response.split(",") if x.strip().isdigit()]
            ranked_docs = [retrieved_docs[i] for i in indices if 0 <= i < len(retrieved_docs)]
            return ranked_docs      # return top 4
        except Exception as e:
            print(f"Reranking error: {e}")
            return retrieved_docs  # return top 4
    

    def answer_query(self, query: str) -> dict:
        """Complete RAG pipeline: retrieval -> reranking -> grounded answering."""
        # 1. Retrieve
        retrieved_docs = self.get_relevant_documents(query)
        if not retrieved_docs:
            return {"response": "I'm sorry, I can't answer that. My knowledge base is not initialized.", "sources": []}
        
        # 2. Rerank
        ranked_docs = self.rerank_documents(query, retrieved_docs)
        top_docs = ranked_docs[:4]
        
        # 3. Answer
        answer_prompt = PromptTemplate.from_template("""
            You are a helpful assistant for {company_name}. Answer the user's question using ONLY the provided context.
            ### Rules:
            1. If the context contains the answer, be concise and professional.
            2. If the context DOES NOT contain the answer, say exactly: "I'm sorry, I don't have specific information about that in my knowledge base."
            3. DO NOT use outside knowledge or hallucinate.
            4. If the user greets you, respond politely and mention you can help with {company_name} services.

            ### Context:
            {context}

            ### User Question:
            "{question}"

            ### Answer:
        """)
        
        context_str = "\n\n".join([f"Source: {doc.metadata['source_url']}\n{doc.page_content}" for doc in top_docs])
        
        chain = answer_prompt | self.answer_llm | StrOutputParser()
        
        try:
            response = chain.invoke({"question": query, "context": context_str, "company_name": COMPANY_NAME})
            sources = list(set([doc.metadata["source_url"] for doc in top_docs]))
            return {
                "response": response,
                "sources": sources
            }
        except Exception as e:
            print(f"Answering error: {e}")
            return {"response": "I encountered an error processing your request.", "sources": []}