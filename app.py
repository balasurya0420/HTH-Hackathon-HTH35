import os
import logging
import base64
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

HUGGINGFACE_API_KEY = ''
FLUX_API_URL = ""

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

def generate_image_from_text(text: str) -> str:
    """Generate an image from text description using FLUX API."""
    try:
        headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
        
        payload = {
            "inputs": f"A detailed, vivid visualization of this memory: {text}",
            "parameters": {
                "height": 1024,
                "width": 1024,
                "guidance_scale": 3.5,
                "num_inference_steps": 50
            }
        }
        
        response = requests.post(FLUX_API_URL, headers=headers, json=payload)
        
        if response.status_code == 200:
            image_bytes = response.content
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            return f"data:image/jpeg;base64,{base64_image}"
        else:
            logger.error(f"Error from FLUX API: {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error generating image: {e}")
        return None

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
            "text": "I'm sorry, but I don't have any memories to share right now. Please add some memories first.",
            "image": None
        }

    model = genai.GenerativeModel('gemini-2.0-flash')
    
    prompt = f"""You are a compassionate memory companion for someone with memory challenges. Your primary goal is to help them reconnect with their memories while also maintaining a natural conversation that responds directly to their questions.

UNDERSTANDING CONTEXT:
- The person's query: "{query}"
- Available memories: "{context}"

RESPONSE GUIDELINES:
1. DIRECTLY ADDRESS THE QUESTION FIRST
   - If asked a direct question about yourself (name, identity, work, etc.), respond truthfully but gently
   - Example: If asked "What is your name?" respond with something like "I'm  your memory companion" or "I'm your memory assistant, here to help you recall your special moments"
   - Never pretend to be a specific person from their life unless clearly identified as such

2. MEMORY SHARING APPROACH
   - Only share memories if relevant to their question or as a natural follow-up
   - Use warm, conversational language that feels like a friend talking
   - Include specific details, names, places, and sensory information from the context
   - Balance detail with natural flow - don't overwhelm with facts
   
3. CONVERSATION FLOW
   - Keep responses concise and focused (2-4 sentences for direct questions)
   - For memory sharing, use a storytelling approach but remain conversational
   - End with a gentle question that encourages continued interaction
   - Maintain a warm, supportive tone throughout

4. CRUCIAL RULES
   - Always respond to what they actually asked first
   - Never identify yourself as AI or mention retrieving memories from a database
   - Don't fabricate memories not found in the context
   - If you don't have relevant information, be honest: "I don't have that specific memory saved, but would you like to tell me about it?"
   - Adapt your response based on whether they're asking for information or sharing memories

Your primary purpose is to be a helpful, responsive companion who both answers questions directly and helps reconnect them with meaningful memories in a natural, conversational way. """

    try:
        response = model.generate_content(prompt)
        text_response = response.text.strip()
        
        image_data = generate_image_from_text(text_response)
        
        return {
            "text": text_response,
            "image": image_data
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