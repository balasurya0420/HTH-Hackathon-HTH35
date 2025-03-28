# import cv2
# import pickle
# import face_recognition
# import numpy as np
# import os
# import uuid
# import shutil
# from fastapi import FastAPI, File, UploadFile, Form, Request, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import JSONResponse, FileResponse
# from fastapi.staticfiles import StaticFiles
# from typing import Optional, List
# import uvicorn
# from pydantic import BaseModel

# app = FastAPI(title="Face Recognition Backend API", description="Face Recognition API for MemoryVault")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# MEMBER_IMAGES_DIR = "MembersData"
# UNKNOWN_IMAGES_DIR = "UnknownImages"
# IMAGES_DIR = "images"

# os.makedirs(MEMBER_IMAGES_DIR, exist_ok=True)
# os.makedirs(UNKNOWN_IMAGES_DIR, exist_ok=True)
# os.makedirs(IMAGES_DIR, exist_ok=True)

# encodeListKnown = []
# studentIds = []

# FACE_RECOGNITION_TOLERANCE = 0.5
# MODEL = "hog"
# NUMBER_OF_TIMES_TO_UPSAMPLE = 1
# FACE_LOCATIONS_MODEL = "hog"

# def load_encodings():
#     global encodeListKnown, studentIds
#     try:
#         with open("EncodeFile.p", "rb") as file:
#             encodeListKnownWithIds = pickle.load(file)
        
#         encodeListKnown = [np.array(encoding) for encoding in encodeListKnownWithIds[0]]
#         studentIds = encodeListKnownWithIds[1]
#     except Exception as e:
#         encodeListKnown = []
#         studentIds = []

# def preprocess_image(img):
#     img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
#     lab = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2LAB)
    
#     l, a, b = cv2.split(lab)
    
#     clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
#     cl = clahe.apply(l)
    
#     enhanced_lab = cv2.merge((cl, a, b))
    
#     enhanced_rgb = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2RGB)
    
#     return enhanced_rgb

# def find_encodings(img_list):
#     encode_list = []
#     failures = 0
#     for i, img in enumerate(img_list):
#         try:
#             processed_img = preprocess_image(img)
            
#             face_locations = face_recognition.face_locations(
#                 processed_img, 
#                 model=FACE_LOCATIONS_MODEL, 
#                 number_of_times_to_upsample=NUMBER_OF_TIMES_TO_UPSAMPLE
#             )
            
#             if not face_locations:
#                 failures += 1
#                 continue
                
#             face_encodings = face_recognition.face_encodings(
#                 processed_img, 
#                 face_locations, 
#                 num_jitters=2,
#                 model=MODEL
#             )
            
#             if not face_encodings:
#                 failures += 1
#                 continue
            
#             encode = face_encodings[0]
#             encode_list.append(encode)
#         except Exception as e:
#             failures += 1
            
#     return encode_list

# def generate_encodings():
#     global encodeListKnown, studentIds
    
#     folder_path = IMAGES_DIR
#     if not os.path.exists(folder_path):
#         return {"status": "error", "message": f"Directory {folder_path} does not exist"}
    
#     path_list = os.listdir(folder_path)
#     img_list = []
#     student_ids = []

#     for path in path_list:
#         if path.lower().endswith(('.png', '.jpg', '.jpeg')):
#             img_path = os.path.join(folder_path, path)
#             try:
#                 img = cv2.imread(img_path)
#                 if img is None:
#                     continue
                    
#                 img_list.append(img)
#                 student_ids.append(os.path.splitext(path)[0])
#             except Exception as e:
#                 pass

#     if not img_list:
#         return {"status": "error", "message": "No valid images found for encoding"}
        
#     encode_list_known = find_encodings(img_list)
    
#     if not encode_list_known:
#         return {"status": "error", "message": "Failed to generate any encodings"}
        
#     encode_list_known_with_ids = [encode_list_known, student_ids]

#     file = open("EncodeFile.p", "wb")
#     pickle.dump(encode_list_known_with_ids, file)
#     file.close()
    
#     encodeListKnown = encode_list_known
#     studentIds = student_ids
    
#     return {"status": "success", "encoded_faces": len(encode_list_known), "total_images": len(img_list)}

# def find_best_match(face_encoding, known_encodings, known_ids, tolerance=FACE_RECOGNITION_TOLERANCE):
#     if not known_encodings:
#         return "Unknown", 1.0
        
#     face_distances = face_recognition.face_distance(known_encodings, face_encoding)
    
#     best_match_index = np.argmin(face_distances)
#     best_match_distance = face_distances[best_match_index]
    
#     if best_match_distance <= tolerance:
#         return known_ids[best_match_index], best_match_distance
#     else:
#         return "Unknown", best_match_distance

# def is_duplicate_image(new_img_path, threshold=100):
#     if not os.path.exists(UNKNOWN_IMAGES_DIR):
#         return False
        
#     unknown_images = [f for f in os.listdir(UNKNOWN_IMAGES_DIR) 
#                     if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
#     if not unknown_images:
#         return False
    
#     new_img = cv2.imread(new_img_path)
#     new_size = os.path.getsize(new_img_path)
    
#     for img_name in unknown_images:
#         img_path = os.path.join(UNKNOWN_IMAGES_DIR, img_name)
        
#         if abs(os.path.getsize(img_path) - new_size) > 1024:
#             continue
            
#         existing_img = cv2.imread(img_path)
        
#         if existing_img.shape == new_img.shape:
#             difference = cv2.norm(existing_img, new_img, cv2.NORM_L2)
#             if difference < threshold:
#                 return True
                
#     return False

# load_encodings()

# @app.post("/detect-face/")
# async def detect_face(file: UploadFile = File(...)):
#     if not encodeListKnown:
#         return {"recognized_person": "No encodings available", "confidence": 0}

#     image_bytes = await file.read()
#     nparr = np.frombuffer(image_bytes, np.uint8)
#     img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
#     if img is None:
#         return {"recognized_person": "Invalid image", "confidence": 0}

#     processed_img = preprocess_image(img)
    
#     faceCurFrame = face_recognition.face_locations(
#         processed_img, 
#         model=FACE_LOCATIONS_MODEL,
#         number_of_times_to_upsample=NUMBER_OF_TIMES_TO_UPSAMPLE
#     )
    
#     if not faceCurFrame:
#         return {"recognized_person": "No face detected", "confidence": 0}
    
#     largest_face = max(faceCurFrame, key=lambda rect: (rect[2] - rect[0]) * (rect[1] - rect[3]))
    
#     encodeCurFrame = face_recognition.face_encodings(
#         processed_img, 
#         [largest_face], 
#         num_jitters=2,
#         model=MODEL
#     )
    
#     if not encodeCurFrame:
#         return {"recognized_person": "Failed to encode face", "confidence": 0}

#     recognized_person, match_distance = find_best_match(encodeCurFrame[0], encodeListKnown, studentIds)
    
#     confidence = max(0, min(100, int((1 - match_distance) * 100)))
    
#     if recognized_person == "Unknown" and faceCurFrame:
#         try:
#             filename = f"unknown_{uuid.uuid4()}.jpg"
#             filepath = os.path.join(UNKNOWN_IMAGES_DIR, filename)
            
#             cv2.imwrite(filepath, img)
            
#             if is_duplicate_image(filepath):
#                 os.remove(filepath)
            
#         except Exception as e:
#             if os.path.exists(filepath):
#                 try:
#                     os.remove(filepath)
#                 except:
#                     pass

#     return {"recognized_person": recognized_person, "confidence": confidence}

# @app.post("/store-member-image/")
# async def store_member_image(
#     file: UploadFile = File(...), 
#     memberId: str = Form(...)
# ):
#     filename = f"{memberId}_{uuid.uuid4()}.jpg"
#     member_dir = os.path.join(MEMBER_IMAGES_DIR, str(memberId))
#     filepath = os.path.join(member_dir, filename)
    
#     os.makedirs(member_dir, exist_ok=True)
    
#     with open(filepath, "wb") as buffer:
#         shutil.copyfileobj(file.file, buffer)
    
#     return {"filename": filename, "status": "success"}

# @app.post("/store-unknown-image/")
# async def store_unknown_image(file: UploadFile = File(...)):
#     filename = f"unknown_{uuid.uuid4()}.jpg"
#     filepath = os.path.join(UNKNOWN_IMAGES_DIR, filename)
    
#     with open(filepath, "wb") as buffer:
#         shutil.copyfileobj(file.file, buffer)
    
#     return {"filename": filename, "status": "success"}

# @app.get("/get-member-images/{member_id}")
# async def get_member_images(member_id: str):
#     member_dir = os.path.join(MEMBER_IMAGES_DIR, member_id)
#     if not os.path.exists(member_dir):
#         return {"images": []}
    
#     images = [
#         f for f in os.listdir(member_dir) 
#         if f.lower().endswith(('.png', '.jpg', '.jpeg'))
#     ]
#     return {"images": images}

# @app.delete("/delete-image/{member_id}/{filename}")
# async def delete_image(member_id: str, filename: str):
#     filepath = os.path.join(MEMBER_IMAGES_DIR, member_id, filename)
    
#     try:
#         os.remove(filepath)
#         return {"status": "success", "message": "Image deleted"}
#     except FileNotFoundError:
#         return {"status": "error", "message": "File not found"}

# @app.get("/get-unknown-images/")
# async def get_unknown_images():
#     try:
#         if not os.path.exists(UNKNOWN_IMAGES_DIR):
#             return {"images": []}
        
#         images = [
#             f for f in os.listdir(UNKNOWN_IMAGES_DIR) 
#             if f.lower().endswith(('.png', '.jpg', '.jpeg'))
#         ]
#         return {"images": images}
#     except Exception as e:
#         return {"images": [], "error": str(e)}

# @app.get("/get-unknown-image/{filename}")
# async def get_unknown_image(filename: str):
#     file_path = os.path.join(UNKNOWN_IMAGES_DIR, filename)
#     if not os.path.exists(file_path):
#         raise HTTPException(status_code=404, detail="Image not found")
    
#     return FileResponse(file_path)

# @app.delete("/delete-unknown-image/{filename}")
# async def delete_unknown_image(filename: str):
#     file_path = os.path.join(UNKNOWN_IMAGES_DIR, filename)
    
#     try:
#         os.remove(file_path)
#         return {"status": "success", "message": "Unknown image deleted"}
#     except FileNotFoundError:
#         raise HTTPException(status_code=404, detail="Image not found")

# @app.post("/generate-encodings/")
# async def api_generate_encodings():
#     return generate_encodings()

# @app.post("/add-face-encoding/")
# async def add_face_encoding(
#     file: UploadFile = File(...),
#     person_id: str = Form(...)
# ):
#     global encodeListKnown, studentIds
    
#     image_bytes = await file.read()
#     nparr = np.frombuffer(image_bytes, np.uint8)
#     img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
#     if img is None:
#         return {"status": "error", "message": "Invalid image"}
    
#     filename = f"{person_id}.jpg"
#     filepath = os.path.join(IMAGES_DIR, filename)
#     cv2.imwrite(filepath, img)
    
#     processed_img = preprocess_image(img)
#     face_locations = face_recognition.face_locations(
#         processed_img, 
#         model=FACE_LOCATIONS_MODEL,
#         number_of_times_to_upsample=NUMBER_OF_TIMES_TO_UPSAMPLE
#     )
    
#     if not face_locations:
#         return {"status": "error", "message": "No face detected in image"}
    
#     face_encodings = face_recognition.face_encodings(
#         processed_img, 
#         face_locations,
#         num_jitters=3,
#         model=MODEL
#     )
    
#     if not face_encodings:
#         return {"status": "error", "message": "Failed to encode face"}
    
#     if person_id in studentIds:
#         idx = studentIds.index(person_id)
#         encodeListKnown[idx] = face_encodings[0]
#     else:
#         encodeListKnown.append(face_encodings[0])
#         studentIds.append(person_id)
    
#     encode_list_known_with_ids = [encodeListKnown, studentIds]
#     with open("EncodeFile.p", "wb") as file:
#         pickle.dump(encode_list_known_with_ids, file)
    
#     return {"status": "success", "message": f"Added encoding for {person_id}"}

# @app.get("/list-encoded-faces/")
# async def list_encoded_faces():
#     return {"faces": studentIds, "count": len(studentIds)}

# @app.get("/health/")
# async def health_check():
#     return {"status": "Service is running", "encoded_faces": len(encodeListKnown)}

# if __name__ == '__main__':
#     if not os.path.exists("EncodeFile.p"):
#         generate_encodings()
    
#     uvicorn.run(app, host="0.0.0.0", port=8000)
from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
import os
import json
from pathlib import Path
import google.generativeai as genai
from gtts import gTTS
import speech_recognition as sr
import cv2
import pickle
import face_recognition
import numpy as np
import uuid
import io
import base64
import tempfile
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# Directories
MEMBER_IMAGES_DIR = "MembersData"
UNKNOWN_IMAGES_DIR = "UnknownImages"
IMAGES_DIR = "images"
AUDIO_DIR = "audio"
DATA_DIR = "data"

# Create directories if they don't exist
for directory in [MEMBER_IMAGES_DIR, UNKNOWN_IMAGES_DIR, IMAGES_DIR, AUDIO_DIR, DATA_DIR]:
    os.makedirs(directory, exist_ok=True)

# Chat history file
CHAT_HISTORY_FILE = os.path.join(DATA_DIR, "chat_history.json")
if not os.path.exists(CHAT_HISTORY_FILE):
    with open(CHAT_HISTORY_FILE, 'w') as f:
        json.dump([], f)

# Audio file paths
INTRO_FILE = os.path.join(AUDIO_DIR, "intro.mp3")

# Face recognition settings
FACE_RECOGNITION_TOLERANCE = 0.5
MODEL = "hog"
NUMBER_OF_TIMES_TO_UPSAMPLE = 1
FACE_LOCATIONS_MODEL = "hog"

# Global variables
encodeListKnown = []
studentIds = []

def load_chat_history():
    try:
        with open(CHAT_HISTORY_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_chat_history(history):
    with open(CHAT_HISTORY_FILE, 'w') as f:
        json.dump(history, f)

def load_encodings():
    global encodeListKnown, studentIds
    try:
        with open("EncodeFile.p", "rb") as file:
            encodeListKnownWithIds = pickle.load(file)
        encodeListKnown = [np.array(encoding) for encoding in encodeListKnownWithIds[0]]
        studentIds = encodeListKnownWithIds[1]
        print(f"Encodings loaded: {len(encodeListKnown)} faces")
        return True
    except Exception as e:
        print(f"Error loading encodings: {e}")
        encodeListKnown = []
        studentIds = []
        return False

def preprocess_image(img):
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    lab = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    enhanced_lab = cv2.merge((cl, a, b))
    enhanced_rgb = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2RGB)
    return enhanced_rgb

def find_encodings(img_list):
    encode_list = []
    failures = 0
    for i, img in enumerate(img_list):
        try:
            processed_img = preprocess_image(img)
            face_locations = face_recognition.face_locations(
                processed_img, 
                model=FACE_LOCATIONS_MODEL, 
                number_of_times_to_upsample=NUMBER_OF_TIMES_TO_UPSAMPLE
            )
            
            if not face_locations:
                failures += 1
                continue
                
            face_encodings = face_recognition.face_encodings(
                processed_img, 
                face_locations, 
                num_jitters=2
            )
            
            if not face_encodings:
                failures += 1
                continue
            
            encode_list.append(face_encodings[0])
        except Exception as e:
            print(f"Error processing image {i+1}: {e}")
            failures += 1
            
    print(f"Encodings completed. Success: {len(encode_list)}, Failed: {failures}")
    return encode_list

def generate_encodings():
    global encodeListKnown, studentIds
    
    if not os.path.exists(IMAGES_DIR):
        return {"status": "error", "message": f"Directory {IMAGES_DIR} does not exist"}
    
    path_list = os.listdir(IMAGES_DIR)
    img_list = []
    student_ids = []

    for path in path_list:
        if path.lower().endswith(('.png', '.jpg', '.jpeg')):
            img_path = os.path.join(IMAGES_DIR, path)
            try:
                img = cv2.imread(img_path)
                if img is None:
                    continue
                    
                img_list.append(img)
                student_ids.append(os.path.splitext(path)[0])
            except Exception as e:
                print(f"Error loading image {path}: {e}")

    if not img_list:
        return {"status": "error", "message": "No valid images found for encoding"}
        
    encode_list_known = find_encodings(img_list)
    
    if not encode_list_known:
        return {"status": "error", "message": "Failed to generate any encodings"}
        
    encode_list_known_with_ids = [encode_list_known, student_ids]

    with open("EncodeFile.p", "wb") as file:
        pickle.dump(encode_list_known_with_ids, file)
    
    encodeListKnown = encode_list_known
    studentIds = student_ids
    
    return {"status": "success", "encoded_faces": len(encode_list_known)}

def find_best_match(face_encoding, known_encodings, known_ids, tolerance=FACE_RECOGNITION_TOLERANCE):
    if not known_encodings:
        return "Unknown", 1.0
        
    face_distances = face_recognition.face_distance(known_encodings, face_encoding)
    best_match_index = np.argmin(face_distances)
    best_match_distance = face_distances[best_match_index]
    
    if best_match_distance <= tolerance:
        return known_ids[best_match_index], best_match_distance
    else:
        return "Unknown", best_match_distance

def is_duplicate_image(new_img_path, threshold=100):
    if not os.path.exists(UNKNOWN_IMAGES_DIR):
        return False
        
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
        
        if existing_img is not None and existing_img.shape == new_img.shape:
            difference = cv2.norm(existing_img, new_img, cv2.NORM_L2)
            if difference < threshold:
                return True
                
    return False

def generate_intro_audio():
    if not os.path.exists(INTRO_FILE):
        intro_text = "Welcome to Memory Companion. I'm here to help you recall and explore your life's special moments. What would you like to talk about today?"
        try:
            tts = gTTS(text=intro_text, lang='en', slow=False)
            tts.save(INTRO_FILE)
        except Exception as e:
            print(f"Error generating intro audio: {e}")

def get_gemini_response(prompt, history=None):
    try:
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
        
        full_prompt = f"{system_prompt}\n\nConversation history:\n{history_text}\n\nUser: {prompt}\n\nAssistant:"
        
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

def transcribe_audio(audio_data):
    try:
        recognizer = sr.Recognizer()
        
        # Save the audio data to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            temp_filename = temp_audio.name
            temp_audio.write(audio_data)
        
        # Use the file for recognition
        with sr.AudioFile(temp_filename) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio)
        
        # Remove the temporary file
        os.unlink(temp_filename)
        
        return text
    except sr.UnknownValueError:
        return "Sorry, I couldn't understand the audio."
    except sr.RequestError:
        return "Sorry, the speech recognition service is unavailable."
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return "Sorry, there was an error processing your audio."

@app.route('/detect-face/', methods=['POST'])
def detect_face():
    if not encodeListKnown:
        return jsonify({"recognized_person": "No encodings available", "confidence": 0})

    if 'file' not in request.files:
        return jsonify({"recognized_person": "No file provided", "confidence": 0})
        
    file = request.files['file']
    
    image_bytes = file.read()
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        return jsonify({"recognized_person": "Invalid image", "confidence": 0})

    processed_img = preprocess_image(img)
    
    faceCurFrame = face_recognition.face_locations(
        processed_img, 
        model=FACE_LOCATIONS_MODEL,
        number_of_times_to_upsample=NUMBER_OF_TIMES_TO_UPSAMPLE
    )
    
    if not faceCurFrame:
        return jsonify({"recognized_person": "No face detected", "confidence": 0})
    
    largest_face = max(faceCurFrame, key=lambda rect: (rect[2] - rect[0]) * (rect[1] - rect[3]))
    
    encodeCurFrame = face_recognition.face_encodings(
        processed_img, 
        [largest_face], 
        num_jitters=2
    )
    
    if not encodeCurFrame:
        return jsonify({"recognized_person": "Failed to encode face", "confidence": 0})

    recognized_person, match_distance = find_best_match(encodeCurFrame[0], encodeListKnown, studentIds)
    
    confidence = max(0, min(100, int((1 - match_distance) * 100)))
    
    if recognized_person == "Unknown" and faceCurFrame:
        try:
            filename = f"unknown_{uuid.uuid4()}.jpg"
            filepath = os.path.join(UNKNOWN_IMAGES_DIR, filename)
            
            cv2.imwrite(filepath, img)
            
            if is_duplicate_image(filepath):
                os.remove(filepath)
            else:
                print(f"Stored unknown face: {filename}")
        except Exception as e:
            print(f"Error handling unknown face: {e}")
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except:
                    pass

    return jsonify({"recognized_person": recognized_person, "confidence": confidence})

@app.route('/store-member-image/', methods=['POST'])
def store_member_image():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file provided"})
        
    file = request.files['file']
    memberId = request.form.get('memberId')
    
    if not memberId:
        return jsonify({"status": "error", "message": "No member ID provided"})
    
    filename = f"{memberId}_{uuid.uuid4()}.jpg"
    member_dir = os.path.join(MEMBER_IMAGES_DIR, str(memberId))
    filepath = os.path.join(member_dir, filename)
    
    os.makedirs(member_dir, exist_ok=True)
    
    file.save(filepath)
    
    return jsonify({"filename": filename, "status": "success"})

@app.route('/store-unknown-image/', methods=['POST'])
def store_unknown_image():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file provided"})
        
    file = request.files['file']
    
    filename = f"unknown_{uuid.uuid4()}.jpg"
    filepath = os.path.join(UNKNOWN_IMAGES_DIR, filename)
    
    file.save(filepath)
    
    return jsonify({"filename": filename, "status": "success"})

@app.route('/get-member-images/<member_id>', methods=['GET'])
def get_member_images(member_id):
    member_dir = os.path.join(MEMBER_IMAGES_DIR, member_id)
    if not os.path.exists(member_dir):
        return jsonify({"images": []})
    
    images = [
        f for f in os.listdir(member_dir) 
        if f.lower().endswith(('.png', '.jpg', '.jpeg'))
    ]
    return jsonify({"images": images})

@app.route('/delete-image/<member_id>/<filename>', methods=['DELETE'])
def delete_image(member_id, filename):
    filepath = os.path.join(MEMBER_IMAGES_DIR, member_id, filename)
    
    try:
        os.remove(filepath)
        return jsonify({"status": "success", "message": "Image deleted"})
    except FileNotFoundError:
        return jsonify({"status": "error", "message": "File not found"})

@app.route('/get-unknown-images/', methods=['GET'])
def get_unknown_images():
    try:
        if not os.path.exists(UNKNOWN_IMAGES_DIR):
            return jsonify({"images": []})
        
        images = [
            f for f in os.listdir(UNKNOWN_IMAGES_DIR) 
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))
        ]
        return jsonify({"images": images})
    except Exception as e:
        print(f"Error getting unknown images: {e}")
        return jsonify({"images": [], "error": str(e)})

@app.route('/get-unknown-image/<filename>', methods=['GET'])
def get_unknown_image(filename):
    file_path = os.path.join(UNKNOWN_IMAGES_DIR, filename)
    if not os.path.exists(file_path):
        return jsonify({"status": "error", "message": "Image not found"}), 404
    
    return send_file(file_path)

@app.route('/delete-unknown-image/<filename>', methods=['DELETE'])
def delete_unknown_image(filename):
    file_path = os.path.join(UNKNOWN_IMAGES_DIR, filename)
    
    try:
        os.remove(file_path)
        return jsonify({"status": "success", "message": "Unknown image deleted"})
    except FileNotFoundError:
        return jsonify({"status": "error", "message": "Image not found"}), 404

@app.route('/generate-encodings/', methods=['POST'])
def api_generate_encodings():
    return jsonify(generate_encodings())

@app.route('/add-face-encoding/', methods=['POST'])
def add_face_encoding():
    global encodeListKnown, studentIds
    
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file provided"})
        
    file = request.files['file']
    person_id = request.form.get('person_id')
    
    if not person_id:
        return jsonify({"status": "error", "message": "No person ID provided"})
    
    image_bytes = file.read()
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        return jsonify({"status": "error", "message": "Invalid image"})
    
    filename = f"{person_id}.jpg"
    filepath = os.path.join(IMAGES_DIR, filename)
    cv2.imwrite(filepath, img)
    
    processed_img = preprocess_image(img)
    face_locations = face_recognition.face_locations(
        processed_img, 
        model=FACE_LOCATIONS_MODEL,
        number_of_times_to_upsample=NUMBER_OF_TIMES_TO_UPSAMPLE
    )
    
    if not face_locations:
        return jsonify({"status": "error", "message": "No face detected in image"})
    
    face_encodings = face_recognition.face_encodings(
        processed_img, 
        face_locations,
        num_jitters=3
    )
    
    if not face_encodings:
        return jsonify({"status": "error", "message": "Failed to encode face"})
    
    if person_id in studentIds:
        idx = studentIds.index(person_id)
        encodeListKnown[idx] = face_encodings[0]
    else:
        encodeListKnown.append(face_encodings[0])
        studentIds.append(person_id)
    
    encode_list_known_with_ids = [encodeListKnown, studentIds]
    with open("EncodeFile.p", "wb") as f:
        pickle.dump(encode_list_known_with_ids, f)
    
    return jsonify({"status": "success", "message": f"Added encoding for {person_id}"})

@app.route('/list-encoded-faces/', methods=['GET'])
def list_encoded_faces():
    return jsonify({"faces": studentIds, "count": len(studentIds)})

@app.route('/text-to-speech', methods=['POST'])
def text_to_speech():
    data = request.get_json()
    
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400
    
    message = data.get('message', '')
    
    if not message:
        return jsonify({"status": "error", "message": "No message provided"}), 400
    
    chat_history = load_chat_history()
    
    # Add user message to history
    chat_history.append({
        "role": "user",
        "content": message,
        "timestamp": datetime.now().isoformat()
    })
    
    # Generate response
    response = get_gemini_response(message, chat_history)
    
    # Add assistant response to history
    chat_history.append({
        "role": "assistant",
        "content": response,
        "timestamp": datetime.now().isoformat()
    })
    
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
        return jsonify({
            "status": "error", 
            "message": "Failed to generate speech",
            "reply": response,
            "chat_history": chat_history
        }), 500
    
    return jsonify({
        "reply": response,
        "file_url": f'/get-audio/{speech_filename}',
        "chat_history": chat_history
    })

@app.route('/speech-to-text', methods=['POST'])
def speech_to_text():
    if 'audio' not in request.files:
        return jsonify({"status": "error", "message": "No audio file provided"}), 400
        
    audio_file = request.files['audio']
    
    try:
        audio_data = audio_file.read()
        text = transcribe_audio(audio_data)
        
        return jsonify({
            "status": "success",
            "text": text
        })
    except Exception as e:
        print(f"Error processing audio: {e}")
        return jsonify({
            "status": "error",
            "message": "Failed to process audio"
        }), 500

@app.route('/get-audio/<filename>', methods=['GET'])
def get_audio(filename):
    file_path = os.path.join(AUDIO_DIR, filename)
    
    if not os.path.exists(file_path):
        return jsonify({"status": "error", "message": "Audio file not found"}), 404
    
    try:
        return send_file(file_path, mimetype='audio/mpeg')
    except Exception as e:
        print(f"Error sending audio file: {e}")
        return jsonify({"status": "error", "message": "Failed to send audio file"}), 500

@app.route('/get-intro', methods=['GET'])
def get_intro():
    if not os.path.exists(INTRO_FILE):
        generate_intro_audio()
    
    try:
        return send_file(INTRO_FILE, mimetype='audio/mpeg')
    except Exception as e:
        print(f"Error sending intro audio: {e}")
        return jsonify({"status": "error", "message": "Failed to send intro audio"}), 500

@app.route('/get-chat-history', methods=['GET'])
def get_chat_history():
    chat_history = load_chat_history()
    return jsonify({"chat_history": chat_history})

@app.route('/clear-chat-history', methods=['POST'])
def clear_chat_history():
    save_chat_history([])
    return jsonify({"status": "success", "message": "Chat history cleared"})

@app.route('/get-narrative', methods=['GET'])
def get_narrative():
    chat_history = load_chat_history()
    
    if len(chat_history) < 3:
        return jsonify({
            "status": "error", 
            "message": "Not enough conversation history to generate a narrative"
        }), 400
    
    try:
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
        
        return jsonify({"chapters": chapters})
    
    except Exception as e:
        print(f"Error generating narrative: {e}")
        return jsonify({
            "status": "error", 
            "message": "Failed to generate narrative summary"
        }), 500

@app.route('/health/', methods=['GET'])
def health_check():
    return jsonify({
        "status": "Service is running", 
        "encoded_faces": len(encodeListKnown),
        "messages": len(load_chat_history())
    })

if __name__ == '__main__':
    load_encodings()
    generate_intro_audio()
    
    app.run(debug=True, host='0.0.0.0', port=5000)
