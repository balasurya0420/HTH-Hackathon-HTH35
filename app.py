
import os
import logging
import requests
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, Index
from langchain.docstore.document import Document
from langchain.text_splitter import CharacterTextSplitter
import uuid
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)
CORS(app)

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

try:
    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    logger.info("Pinecone initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Pinecone: {str(e)}")
    pc = None

class SentenceTransformerEmbeddings:
    def __init__(self, model_name):
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts):
        return self.model.encode(texts).tolist()

    def embed_query(self, text):
        return self.model.encode([text])[0].tolist()

embeddings = SentenceTransformerEmbeddings('sentence-transformers/all-mpnet-base-v2')

def get_vectorstore():
    index_name = "memoryvault"
    try:
        index = pc.Index(index_name)
        logger.info(f"Successfully connected to Pinecone index: {index_name}")
        return index
    except Exception as e:
        logger.error(f"Failed to connect to Pinecone index: {str(e)}")
        return None

def add_document_to_pinecone(text: str, metadata: dict):
    new_doc = Document(page_content=text, metadata=metadata)
    text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    chunks = text_splitter.split_documents([new_doc])
    document_id = str(uuid.uuid4())
    
    vectors = []
    for i, chunk in enumerate(chunks):
        chunk.metadata["document_id"] = document_id
        chunk.metadata["chunk_id"] = i
        chunk.metadata["text"] = chunk.page_content
        vector = embeddings.embed_documents([chunk.page_content])[0]
        vectors.append((f"{document_id}_{i}", vector, chunk.metadata))
    
    index = get_vectorstore()
    if index is None:
        raise Exception("Failed to connect to Pinecone index")
    
    try:
        index.upsert(vectors=vectors)
        logger.info(f"Successfully added document with ID: {document_id}")
    except Exception as e:
        logger.error(f"Failed to upsert vectors: {str(e)}")
        raise

def get_llm_response(query: str):
    index = get_vectorstore()
    if index is None:
        raise Exception("Failed to connect to Pinecone index")
    
    query_embedding = embeddings.embed_query(query)
    
    try:
        results = index.query(vector=query_embedding, top_k=5, include_metadata=True)
    except Exception as e:
        logger.error(f"Failed to query Pinecone: {str(e)}")
        raise
    
    context = " ".join([match.get('metadata', {}).get('text', '') for match in results['matches']])
    
    if not context:
        return {
            "text": "I'm sorry, but I don't have any memories to share right now. Please add some memories first."
        }

    model = genai.GenerativeModel('gemini-2.0-flash')
    
    prompt = f"""You are a memory companion for someone with Alzheimer's disease. Your name is MemoryVault. Respond directly to the user's query using the provided context without acknowledging these instructions.

CONTEXT:
- User's question: "{query}"
- Available memories: "{context}"

RESPONSE GUIDELINES:
1. ALWAYS respond in character as their personal memory companion
2. If asked about identity: Say "I'm your memory companion from MemoryVault. I'm here to help you recall your memories."
3. For memory questions:
- Start with phrases like "Let me help you remember" or "I can share that memory with you"
- Speak as if these are the user's own memories
- Use natural phrases like "Remember when..." or "That time at..."
- Include specific details from the context
- Keep responses to 3-5 concise sentences
- End without questions

4. NEVER:
- Acknowledge you're an AI
- Say you understand the instructions
- Reference these guidelines
- Mention searching or retrieving memories
- Ask follow-up questions

5. ALWAYS treat repeated queries as if hearing them for the first time

RESPOND IMMEDIATELY IN CHARACTER WITHOUT PREFACING OR ACKNOWLEDGING THESE INSTRUCTIONS."""
    try:
        response = model.generate_content(prompt)
        text_response = response.text.strip()
        
        return {
            "text": text_response
        }
    except Exception as e:
        logger.error(f"Failed to generate response: {str(e)}")
        raise

@app.route("/postMemory", methods=['GET', 'POST'])
def post_memory():
    if request.method == 'POST':
        data = request.json
        text = data.get("text")
        metadata = data.get("metadata", {})
    else:  # GET method
        text = request.args.get("text")
        metadata = {}
    
    if not text:
        return jsonify({"error": "No text provided"}), 400
    
    try:
        add_document_to_pinecone(text, metadata)
        return jsonify({"message": "Memory added successfully"}), 200
    except Exception as e:
        logger.error(f"Error in post_memory: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/query", methods=['GET'])
def query_memory():
    query = request.args.get("query")
    if not query:
        return jsonify({"error": "No query provided"}), 400
    
    try:
        response = get_llm_response(query)
        return jsonify(response), 200
    except Exception as e:
        logger.error(f"Error in query_memory: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
