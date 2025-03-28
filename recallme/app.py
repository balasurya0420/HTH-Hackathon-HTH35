
from fastapi import FastAPI, File, UploadFile, Form, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional, List, Dict, Any
import uvicorn
from pydantic import BaseModel
import os
import json
import base64
from io import BytesIO
import google.generativeai as genai
from gtts import gTTS
import speech_recognition as sr
import tempfile
from datetime import datetime
import uuid
import shutil
import cv2
import pickle
import face_recognition
import numpy as np

# Create the FastAPI app
app = FastAPI(title="Memory Companion with Face Recognition", description="Integrated API for Memory Companion")

# Configure CORS - Allow the React frontend to access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("WARNING: GEMINI_API_KEY not found in environment variables")

# Directories
AUDIO_DIR = "audio"
DATA_DIR = "data"
MEMBER_IMAGES_DIR = "MembersData"
UNKNOWN_IMAGES_DIR = "UnknownImages"
IMAGES_DIR = "images"

# Create directories if they don't exist
for directory in [AUDIO_DIR, DATA_DIR, MEMBER_IMAGES_DIR, UNKNOWN_IMAGES_DIR, IMAGES_DIR]:
    os.makedirs(directory, exist_ok=True)

# Chat history file
CHAT_HISTORY_FILE = os.path.join(DATA_DIR, "chat_history.json")
if not os.path.exists(CHAT_HISTORY_FILE):
    with open(CHAT_HISTORY_FILE, 'w') as f:
        json.dump([], f)

# Audio file paths
INTRO_FILE = os.path.join(AUDIO_DIR, "intro.mp3")

# Face recognition settings
FACE_RECOGNITION_TOLERANCE = 0.5  # Lower value means stricter matching
MODEL = "hog"  # Options: 'hog' (faster) or 'cnn' (more accurate, requires GPU)
NUMBER_OF_TIMES_TO_UPSAMPLE = 1
FACE_LOCATIONS_MODEL = "hog"

# Global variables for face encoding
encodeListKnown = []
studentIds = []

# Request models
class TextToSpeechRequest(BaseModel):
    message: str
    face_image: Optional[str] = None

class ClearHistoryResponse(BaseModel):
    status: str
    message: str

#================ MEMORY COMPANION FUNCTIONS ================

def load_chat_history():
    try:
        with open(CHAT_HISTORY_FILE, 'r') as f:
            history = json.load(f)
            # Add IDs to messages if they don't have them
            for i, msg in enumerate(history):
                if 'id' not in msg:
                    msg['id'] = f"msg-{i}"
            return history
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_chat_history(history):
    with open(CHAT_HISTORY_FILE, 'w') as f:
        json.dump(history, f)

def generate_intro_audio():
    if not os.path.exists(INTRO_FILE):
        intro_text = "Welcome to Memory Companion. I'm here to help you recall and explore your life's special moments. What would you like to talk about today?"
        try:
            tts = gTTS(text=intro_text, lang='en', slow=False)
            tts.save(INTRO_FILE)
            print(f"Generated intro audio at {INTRO_FILE}")
        except Exception as e:
            print(f"Error generating intro audio: {e}")

def get_gemini_response(prompt, history=None, recognized_person=None):
    try:
        if not GEMINI_API_KEY:
            return "I'm sorry, but I can't connect to my AI service right now. Please make sure the GEMINI_API_KEY is configured."
            
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        system_prompt = """
        You are a compassionate care assistant helping someone with memory recall. Be gentle, empathetic, and thoughtful.
        
        IMPORTANT FORMATTING RULES:
        1. Write in a natural, conversational style
        2. Avoid using symbols like ', ", ?, ! in ways that would sound awkward when read aloud
        3. Use simple punctuation and natural phrases
        4. Don't include symbols or characters that would sound strange when spoken
        5. Keep responses concise and directly address the person's thoughts
        6. Format lists and information in a way that sounds natural when spoken
        7. Your responses should be compassionate but brief (3-5 sentences maximum)
        """
        
        if not history:
            history = []
            
        history_text = "\n".join([f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}" for msg in history[-5:]])
        
        context = ""
        if recognized_person and recognized_person != "Unknown" and recognized_person != "No face detected" and recognized_person != "No encodings available":
            context = f"\nThe person you are speaking with has been recognized as: {recognized_person}."
        
        full_prompt = f"{system_prompt}\n\nConversation history:\n{history_text}{context}\n\nUser: {prompt}\n\nAssistant:"
        
        response = model.generate_content(full_prompt, generation_config={
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 300,
        })
        
        # Clean up response for TTS
        clean_response = response.text.strip()
        
        return clean_response
    except Exception as e:
        print(f"Error with Gemini: {e}")
        return "I'm sorry, I'm having trouble processing that right now. Could you try again?"

#================ FACE RECOGNITION FUNCTIONS ================

def load_encodings():
    global encodeListKnown, studentIds
    print("Loading Encoded File ...")
    try:
        if os.path.exists("EncodeFile.p"):
            with open("EncodeFile.p", "rb") as file:
                encodeListKnownWithIds = pickle.load(file)
            
            # Ensure encodings are numpy arrays
            encodeListKnown = [np.array(encoding) for encoding in encodeListKnownWithIds[0]]
            studentIds = encodeListKnownWithIds[1]
            print(f"Encode File Loaded Successfully: {len(encodeListKnown)} faces")
        else:
            print("No encoding file found. Will create one when images are added.")
    except Exception as e:
        print(f"Error loading encoding file: {e}")
        encodeListKnown = []
        studentIds = []

def preprocess_image(img):
    # Convert to RGB (face_recognition uses RGB)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # Optional: Enhance contrast for better face detection
    # Convert to LAB color space
    lab = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2LAB)
    
    # Split the LAB image into L, A, and B channels
    l, a, b = cv2.split(lab)
    
    # Apply CLAHE to the L channel
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    
    # Merge the CLAHE enhanced L channel with original A and B channels
    enhanced_lab = cv2.merge((cl, a, b))
    
    # Convert back to RGB
    enhanced_rgb = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2RGB)
    
    return enhanced_rgb

def find_encodings(img_list):
    encode_list = []
    failures = 0
    for i, img in enumerate(img_list):
        try:
            # Preprocess image for better face detection
            processed_img = preprocess_image(img)
            
            # Detect face locations with more aggressive detection
            face_locations = face_recognition.face_locations(
                processed_img, 
                model=FACE_LOCATIONS_MODEL, 
                number_of_times_to_upsample=NUMBER_OF_TIMES_TO_UPSAMPLE
            )
            
            if not face_locations:
                print(f"No face found in image {i+1}")
                failures += 1
                continue
                
            # Get all face encodings
            face_encodings = face_recognition.face_encodings(
                processed_img, 
                face_locations, 
                num_jitters=2,  # Multiple samples for more accurate encoding
                model=MODEL
            )
            
            if not face_encodings:
                print(f"Failed to encode face in image {i+1}")
                failures += 1
                continue
            
            # Take the first face encoding
            encode = face_encodings[0]
            encode_list.append(encode)
            print(f"Successfully encoded face {i+1}")
        except Exception as e:
            print(f"Error processing image {i+1}: {e}")
            failures += 1
            
    print(f"Encodings completed. Successful: {len(encode_list)}, Failed: {failures}")
    return encode_list

def generate_encodings():
    global encodeListKnown, studentIds
    
    folder_path = IMAGES_DIR
    if not os.path.exists(folder_path):
        print(f"Error: Directory {folder_path} does not exist")
        return {"status": "error", "message": f"Directory {folder_path} does not exist"}
    
    path_list = os.listdir(folder_path)
    img_list = []
    student_ids = []

    print(f"Found {len(path_list)} items in {folder_path}")
    
    for path in path_list:
        if path.lower().endswith(('.png', '.jpg', '.jpeg')):
            img_path = os.path.join(folder_path, path)
            try:
                img = cv2.imread(img_path)
                if img is None:
                    print(f"Failed to read image {path}")
                    continue
                    
                img_list.append(img)
                student_ids.append(os.path.splitext(path)[0])
                print(f"Added image {path} for encoding")
            except Exception as e:
                print(f"Error loading image {path}: {e}")

    if not img_list:
        print("No valid images found for encoding")
        return {"status": "error", "message": "No valid images found for encoding"}
        
    print(f"Encoding {len(img_list)} images...")
    encode_list_known = find_encodings(img_list)
    
    if not encode_list_known:
        print("Failed to generate any encodings")
        return {"status": "error", "message": "Failed to generate any encodings"}
        
    encode_list_known_with_ids = [encode_list_known, student_ids]
    print("Encoding Complete")

    with open("EncodeFile.p", "wb") as file:
        pickle.dump(encode_list_known_with_ids, file)
    print("File Saved")
    
    # Update global variables
    encodeListKnown = encode_list_known
    studentIds = student_ids
    
    return {"status": "success", "encoded_faces": len(encode_list_known), "total_images": len(img_list)}

def find_best_match(face_encoding, known_encodings, known_ids, tolerance=FACE_RECOGNITION_TOLERANCE):
    if not known_encodings:
        return "Unknown", 1.0
        
    # Calculate face distances
    face_distances = face_recognition.face_distance(known_encodings, face_encoding)
    
    # Find best match index
    best_match_index = np.argmin(face_distances)
    best_match_distance = face_distances[best_match_index]
    
    # If distance is below tolerance, return the ID
    if best_match_distance <= tolerance:
        return known_ids[best_match_index], best_match_distance
    else:
        return "Unknown", best_match_distance

def is_duplicate_image(new_img_path, threshold=100):
    if not os.path.exists(UNKNOWN_IMAGES_DIR):
        return False
        
    # Get list of existing unknown images
    unknown_images = [f for f in os.listdir(UNKNOWN_IMAGES_DIR) 
                    if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    if not unknown_images:
        return False
    
    new_img = cv2.imread(new_img_path)
    new_size = os.path.getsize(new_img_path)
    
    for img_name in unknown_images:
        img_path = os.path.join(UNKNOWN_IMAGES_DIR, img_name)
        
        if abs(os.path.getsize(img_path) - new_size) > 1024:
            continue
            
        existing_img = cv2.imread(img_path)
        
        if existing_img.shape == new_img.shape:
            difference = cv2.norm(existing_img, new_img, cv2.NORM_L2)
            if difference < threshold:
                return True
                
    return False

#================ API ENDPOINTS ================

# Initialize the app on startup
@app.on_event("startup")
async def startup_event():
    print("Starting up the server...")
    # Load face encodings
    load_encodings()
    # Generate intro audio
    generate_intro_audio()
    print("Server initialization complete")

#-------- Memory Companion Endpoints --------

@app.post("/speech-to-text")
async def speech_to_text(audio: UploadFile = File(...)):
    if not audio:
        return JSONResponse({"status": "error", "message": "No audio file provided"}, status_code=400)
        
    recognizer = sr.Recognizer()
    
    # Create a temporary file in binary write mode
    temp_file = None
    try:
        # Save the file to a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.close()  # Close the file handle immediately
        
        # Read the file content
        audio_content = await audio.read()
        
        # Write to the temporary file
        with open(temp_file.name, 'wb') as f:
            f.write(audio_content)
        
        # Try direct recognition with Google API
        try:
            with sr.AudioFile(temp_file.name) as source:
                audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data)
                return JSONResponse({"status": "success", "text": text})
        except sr.UnknownValueError:
            return JSONResponse({"status": "error", "message": "Could not understand audio"}, status_code=400)
        except Exception as e:
            print(f"Error in speech recognition: {str(e)}")
            return JSONResponse({"status": "error", "message": "Could not process audio format"}, status_code=400)
    except Exception as e:
        print(f"File handling error: {str(e)}")
        return JSONResponse({"status": "error", "message": "Failed to process audio file"}, status_code=500)
    finally:
        # Clean up temporary file - use try/except to handle any file access errors
        if temp_file:
            try:
                import time
                time.sleep(0.1)  # Small delay to ensure file is not in use
                os.unlink(temp_file.name)
            except Exception as e:
                print(f"Warning: Could not delete temporary file: {str(e)}")

@app.post("/text-to-speech")
async def text_to_speech(request: Request):
    data = await request.json()
    
    if not data:
        return JSONResponse({"status": "error", "message": "No data provided"}, status_code=400)
    
    message = data.get('message', '')
    face_image = data.get('face_image', None)
    
    if not message:
        return JSONResponse({"status": "error", "message": "No message provided"}, status_code=400)
    
    # Get recognized person from face image if provided
    recognized_person = None
    confidence = 0
    
    if face_image:
        # Process the face image (base64 encoded)
        try:
            # Convert base64 to image
            # Remove the data URL prefix if present
            if "," in face_image:
                face_image = face_image.split(",")[1]
                
            img_data = base64.b64decode(face_image)
            nparr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is not None:
                # Process image for face recognition
                processed_img = preprocess_image(img)
                face_locations = face_recognition.face_locations(
                    processed_img, 
                    model=FACE_LOCATIONS_MODEL,
                    number_of_times_to_upsample=NUMBER_OF_TIMES_TO_UPSAMPLE
                )
                
                if face_locations:
                    largest_face = max(face_locations, key=lambda rect: (rect[2] - rect[0]) * (rect[1] - rect[3]))
                    
                    face_encodings = face_recognition.face_encodings(
                        processed_img, 
                        [largest_face], 
                        num_jitters=2,
                        model=MODEL
                    )
                    
                    if face_encodings:
                        recognized_person, match_distance = find_best_match(face_encodings[0], encodeListKnown, studentIds)
                        confidence = max(0, min(100, int((1 - match_distance) * 100)))
                        
                        # Store unknown face if confidence is low
                        if recognized_person == "Unknown":
                            try:
                                filename = f"unknown_{uuid.uuid4()}.jpg"
                                filepath = os.path.join(UNKNOWN_IMAGES_DIR, filename)
                                
                                cv2.imwrite(filepath, img)
                                
                                if is_duplicate_image(filepath):
                                    os.remove(filepath)
                            except Exception as e:
                                print(f"Error storing unknown face: {e}")
                    else:
                        recognized_person = "Failed to encode face"
                else:
                    recognized_person = "No face detected"
        except Exception as e:
            print(f"Error in face recognition: {e}")
            recognized_person = None
    
    chat_history = load_chat_history()
    
    # Add user message to history with a unique ID
    user_message_id = f"user-{uuid.uuid4()}"
    userMessage = {
        "id": user_message_id,
        "role": "user", 
        "content": message,
        "timestamp": datetime.now().isoformat()
    }
    chat_history.append(userMessage)
    
    # Generate response
    response = get_gemini_response(message, chat_history, recognized_person)
    
    # Add assistant response to history with a unique ID
    assistant_message_id = f"assistant-{uuid.uuid4()}"
    assistantMessage = {
        "id": assistant_message_id,
        "role": "assistant", 
        "content": response,
        "timestamp": datetime.now().isoformat()
    }
    chat_history.append(assistantMessage)
    
    # Save updated history
    save_chat_history(chat_history)
    
    # Generate speech
    speech_filename = f"response_{len(chat_history)}.mp3"
    speech_filepath = os.path.join(AUDIO_DIR, speech_filename)
    
    try:
        tts = gTTS(text=response, lang='en', slow=False)
        tts.save(speech_filepath)
    except Exception as e:
        print(f"Error generating speech: {e}")
        return JSONResponse({
            "status": "error", 
            "message": "Failed to generate speech",
            "reply": response,
            "chat_history": chat_history,
            "recognized_person": recognized_person,
            "confidence": confidence
        }, status_code=500)
    
    return JSONResponse({
        "reply": response,
        "file_url": f'/get-audio/{speech_filename}',
        "chat_history": chat_history,
        "recognized_person": recognized_person,
        "confidence": confidence
    })

@app.get("/get-audio/{filename}")
async def get_audio(filename: str):
    file_path = os.path.join(AUDIO_DIR, filename)
    
    if not os.path.exists(file_path):
        return JSONResponse({"status": "error", "message": "Audio file not found"}, status_code=404)
    
    try:
        return FileResponse(file_path, media_type='audio/mpeg')
    except Exception as e:
        print(f"Error sending audio file: {e}")
        return JSONResponse({"status": "error", "message": "Failed to send audio file"}, status_code=500)

@app.get("/get-intro")
async def get_intro():
    if not os.path.exists(INTRO_FILE):
        generate_intro_audio()
    
    try:
        return FileResponse(INTRO_FILE, media_type='audio/mpeg')
    except Exception as e:
        print(f"Error sending intro audio: {e}")
        return JSONResponse({"status": "error", "message": "Failed to send intro audio"}, status_code=500)

@app.get("/get-chat-history")
async def get_chat_history():
    chat_history = load_chat_history()
    return JSONResponse({"chat_history": chat_history})

@app.post("/clear-chat-history")
async def clear_chat_history():
    save_chat_history([])
    return JSONResponse({"status": "success", "message": "Chat history cleared"})

@app.get("/get-narrative")
async def get_narrative():
    chat_history = load_chat_history()
    
    if len(chat_history) < 3:
        return JSONResponse({
            "status": "error", 
            "message": "Not enough conversation history to generate a narrative"
        }, status_code=400)
    
    try:
        if not GEMINI_API_KEY:
            return JSONResponse({
                "status": "error", 
                "message": "GEMINI_API_KEY not configured"
            }, status_code=500)
            
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        narrative_prompt = """
        You are a compassionate storyteller and reminiscence therapist. Your task is to craft a deeply personal 
        and heartfelt narrative based on the provided memories and experiences below. Write in a warm, 
        conversational tone, as if you're speaking directly to the individual.
        
        Highlight moments of joy, pride, love, and connection, focusing on the emotions and the essence 
        of the memories rather than just the facts. Keep each section concise - no more than two sentences per topic.
        
        Make the narrative feel like the person's unique story, celebrating their resilience, growth,
        and the things that bring them happiness. The final story should feel comforting, affirming, and personal.
        
        Separate the story into 3-5 distinct sections, each focused on a different aspect or memory.
        Return these sections separated by -- symbols.
        """
        
        history_text = "\n".join([f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}" for msg in chat_history])
        
        full_prompt = f"{narrative_prompt}\n\nConversation history:\n{history_text}"
        
        response = model.generate_content(full_prompt, generation_config={
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 1024,
        })
        
        narrative = response.text.strip()
        
        # Split into chapters
        chapters = narrative.split("--")
        chapters = [chapter.strip() for chapter in chapters if chapter.strip()]
        
        return JSONResponse({"chapters": chapters})
    
    except Exception as e:
        print(f"Error generating narrative: {e}")
        return JSONResponse({
            "status": "error", 
            "message": f"Failed to generate narrative summary: {str(e)}"
        }, status_code=500)

#-------- Face Recognition Endpoints --------

@app.post("/detect-face/")
async def detect_face(file: UploadFile = File(...)):
    # Check if any encodings are available
    if not encodeListKnown:
        return JSONResponse({"recognized_person": "No encodings available", "confidence": 0})

    # Read image bytes
    image_bytes = await file.read()
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        return JSONResponse({"recognized_person": "Invalid image", "confidence": 0})

    # Preprocess the image
    processed_img = preprocess_image(img)
    
    # Detect face locations with multiple upsampling for better detection
    faceCurFrame = face_recognition.face_locations(
        processed_img, 
        model=FACE_LOCATIONS_MODEL,
        number_of_times_to_upsample=NUMBER_OF_TIMES_TO_UPSAMPLE
    )
    
    if not faceCurFrame:
        return JSONResponse({"recognized_person": "No face detected", "confidence": 0})
    
    # Get the largest face (assuming it's the main subject)
    largest_face = max(faceCurFrame, key=lambda rect: (rect[2] - rect[0]) * (rect[1] - rect[3]))
    
    # Encode the face with multiple samples for better accuracy
    encodeCurFrame = face_recognition.face_encodings(
        processed_img, 
        [largest_face], 
        num_jitters=2,  # Multiple samples for more accurate encoding
        model=MODEL
    )
    
    if not encodeCurFrame:
        return JSONResponse({"recognized_person": "Failed to encode face", "confidence": 0})

    # Find the best match
    recognized_person, match_distance = find_best_match(encodeCurFrame[0], encodeListKnown, studentIds)
    
    # Calculate confidence (1.0 is worst match, 0.0 is perfect match)
    confidence = max(0, min(100, int((1 - match_distance) * 100)))
    
    print(f"Recognized: {recognized_person}, Confidence: {confidence}%")
    
    # If face is not recognized with sufficient confidence, store it in unknown faces
    if recognized_person == "Unknown" and faceCurFrame:
        try:
            # Generate unique filename
            filename = f"unknown_{uuid.uuid4()}.jpg"
            filepath = os.path.join(UNKNOWN_IMAGES_DIR, filename)
            
            # Save file temporarily
            cv2.imwrite(filepath, img)
            
            # Check if this is a duplicate of an existing unknown image
            if is_duplicate_image(filepath):
                os.remove(filepath)
                print("Duplicate unknown face detected - not storing")
            else:
                print(f"Stored unknown face: {filename}")
        except Exception as e:
            print(f"Error handling unknown face: {e}")
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except:
                    pass

    return JSONResponse({"recognized_person": recognized_person, "confidence": confidence})

@app.post("/store-member-image/")
async def store_member_image(
    file: UploadFile = File(...), 
    memberId: str = Form(...)
):
    # Generate unique filename
    filename = f"{memberId}_{uuid.uuid4()}.jpg"
    member_dir = os.path.join(MEMBER_IMAGES_DIR, str(memberId))
    filepath = os.path.join(member_dir, filename)
    
    # Ensure member directory exists
    os.makedirs(member_dir, exist_ok=True)
    
    # Save file
    content = await file.read()
    with open(filepath, "wb") as buffer:
        buffer.write(content)
    
    return JSONResponse({"filename": filename, "status": "success"})

@app.post("/store-unknown-image/")
async def store_unknown_image(file: UploadFile = File(...)):
    # Generate unique filename
    filename = f"unknown_{uuid.uuid4()}.jpg"
    filepath = os.path.join(UNKNOWN_IMAGES_DIR, filename)
    
    # Save file
    content = await file.read()
    with open(filepath, "wb") as buffer:
        buffer.write(content)
    
    return JSONResponse({"filename": filename, "status": "success"})

@app.get("/get-member-images/{member_id}")
async def get_member_images(member_id: str):
    member_dir = os.path.join(MEMBER_IMAGES_DIR, member_id)
    if not os.path.exists(member_dir):
        return JSONResponse({"images": []})
    
    images = [
        f for f in os.listdir(member_dir) 
        if f.lower().endswith(('.png', '.jpg', '.jpeg'))
    ]
    return JSONResponse({"images": images})

@app.delete("/delete-image/{member_id}/{filename}")
async def delete_image(member_id: str, filename: str):
    filepath = os.path.join(MEMBER_IMAGES_DIR, member_id, filename)
    
    try:
        os.remove(filepath)
        return JSONResponse({"status": "success", "message": "Image deleted"})
    except FileNotFoundError:
        return JSONResponse({"status": "error", "message": "File not found"})

@app.get("/get-unknown-images/")
async def get_unknown_images():
    """Get list of all unknown images"""
    try:
        if not os.path.exists(UNKNOWN_IMAGES_DIR):
            return JSONResponse({"images": []})
        
        images = [
            f for f in os.listdir(UNKNOWN_IMAGES_DIR) 
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))
        ]
        return JSONResponse({"images": images})
    except Exception as e:
        print(f"Error getting unknown images: {e}")
        return JSONResponse({"images": [], "error": str(e)})

@app.get("/get-unknown-image/{filename}")
async def get_unknown_image(filename: str):
    """Get a specific unknown image file"""
    file_path = os.path.join(UNKNOWN_IMAGES_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Return the image file
    return FileResponse(file_path)

@app.delete("/delete-unknown-image/{filename}")
async def delete_unknown_image(filename: str):
    """Delete an unknown image"""
    file_path = os.path.join(UNKNOWN_IMAGES_DIR, filename)
    
    try:
        os.remove(file_path)
        return JSONResponse({"status": "success", "message": "Unknown image deleted"})
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Image not found")

# Endpoint to regenerate encodings
@app.post("/generate-encodings/")
async def api_generate_encodings():
    return generate_encodings()

# Endpoint to add a single image to the encodings
@app.post("/add-face-encoding/")
async def add_face_encoding(
    file: UploadFile = File(...),
    person_id: str = Form(...)
):
    global encodeListKnown, studentIds
    
    # Read image bytes
    image_bytes = await file.read()
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        return JSONResponse({"status": "error", "message": "Invalid image"})
    
    # Save to images directory
    filename = f"{person_id}.jpg"
    filepath = os.path.join(IMAGES_DIR, filename)
    cv2.imwrite(filepath, img)
    
    # Generate encoding for this image
    processed_img = preprocess_image(img)
    face_locations = face_recognition.face_locations(
        processed_img, 
        model=FACE_LOCATIONS_MODEL,
        number_of_times_to_upsample=NUMBER_OF_TIMES_TO_UPSAMPLE
    )
    
    if not face_locations:
        return JSONResponse({"status": "error", "message": "No face detected in image"})
    
    face_encodings = face_recognition.face_encodings(
        processed_img, 
        face_locations,
        num_jitters=3,  # Multiple samples for more accurate encoding
        model=MODEL
    )
    
    if not face_encodings:
        return JSONResponse({"status": "error", "message": "Failed to encode face"})
    
    # Add to current encodings
    if person_id in studentIds:
        # Replace existing encoding
        idx = studentIds.index(person_id)
        encodeListKnown[idx] = face_encodings[0]
    else:
        # Add new encoding
        encodeListKnown.append(face_encodings[0])
        studentIds.append(person_id)
    
    # Save updated encodings
    encode_list_known_with_ids = [encodeListKnown, studentIds]
    with open("EncodeFile.p", "wb") as file:
        pickle.dump(encode_list_known_with_ids, file)
    
    return JSONResponse({"status": "success", "message": f"Added encoding for {person_id}"})

@app.get("/list-encoded-faces/")
async def list_encoded_faces():
    """List all encoded faces"""
    return JSONResponse({"faces": studentIds, "count": len(studentIds)})

@app.get("/health/")
async def health_check():
    """Health check endpoint for the service"""
    return JSONResponse({
        "status": "Service is running", 
        "encoded_faces": len(encodeListKnown),
        "messages": len(load_chat_history())
    })

# Endpoint to update Frontend API port (defaults to 5000)
@app.post("/update-frontend-port/")
async def update_frontend_port(request: Request):
    data = await request.json()
    port = data.get('port', 5000)
    
    # Write port to a config file for persistence
    try:
        with open(os.path.join(DATA_DIR, "config.json"), 'w') as f:
            json.dump({"frontend_port": port}, f)
        return JSONResponse({"status": "success", "message": f"Frontend port updated to {port}"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": f"Failed to update port: {str(e)}"})

# Main entry point
if __name__ == '__main__':
    # Make sure directories exist
    for directory in [AUDIO_DIR, DATA_DIR, MEMBER_IMAGES_DIR, UNKNOWN_IMAGES_DIR, IMAGES_DIR]:
        os.makedirs(directory, exist_ok=True)
        
    # Generate encodings if the encode file doesn't exist
    if not os.path.exists("EncodeFile.p"):
        print("No encoding file found. Creating default encodings...")
        generate_encodings()
    else:
        # Load existing encodings
        print("Loading existing encodings...")
        load_encodings()
        
    # Generate intro audio if needed
    if not os.path.exists(INTRO_FILE):
        print("Generating intro audio...")
        generate_intro_audio()
    
    # Run the FastAPI app with uvicorn
    print("Starting server on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
