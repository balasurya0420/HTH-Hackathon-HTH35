import cv2
import pickle
import face_recognition
import numpy as np
import os
import uuid
import shutil
from fastapi import FastAPI, File, UploadFile, Form, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional, List
import uvicorn
from pydantic import BaseModel

app = FastAPI(title="Face Recognition Backend API", description="Face Recognition API for MemoryVault")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MEMBER_IMAGES_DIR = "MembersData"
UNKNOWN_IMAGES_DIR = "UnknownImages"
IMAGES_DIR = "images"

os.makedirs(MEMBER_IMAGES_DIR, exist_ok=True)
os.makedirs(UNKNOWN_IMAGES_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

encodeListKnown = []
studentIds = []

FACE_RECOGNITION_TOLERANCE = 0.5
MODEL = "hog"
NUMBER_OF_TIMES_TO_UPSAMPLE = 1
FACE_LOCATIONS_MODEL = "hog"

def load_encodings():
    global encodeListKnown, studentIds
    try:
        with open("EncodeFile.p", "rb") as file:
            encodeListKnownWithIds = pickle.load(file)
        
        encodeListKnown = [np.array(encoding) for encoding in encodeListKnownWithIds[0]]
        studentIds = encodeListKnownWithIds[1]
    except Exception as e:
        encodeListKnown = []
        studentIds = []

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
                num_jitters=2,
                model=MODEL
            )
            
            if not face_encodings:
                failures += 1
                continue
            
            encode = face_encodings[0]
            encode_list.append(encode)
        except Exception as e:
            failures += 1
            
    return encode_list

def generate_encodings():
    global encodeListKnown, studentIds
    
    folder_path = IMAGES_DIR
    if not os.path.exists(folder_path):
        return {"status": "error", "message": f"Directory {folder_path} does not exist"}
    
    path_list = os.listdir(folder_path)
    img_list = []
    student_ids = []

    for path in path_list:
        if path.lower().endswith(('.png', '.jpg', '.jpeg')):
            img_path = os.path.join(folder_path, path)
            try:
                img = cv2.imread(img_path)
                if img is None:
                    continue
                    
                img_list.append(img)
                student_ids.append(os.path.splitext(path)[0])
            except Exception as e:
                pass

    if not img_list:
        return {"status": "error", "message": "No valid images found for encoding"}
        
    encode_list_known = find_encodings(img_list)
    
    if not encode_list_known:
        return {"status": "error", "message": "Failed to generate any encodings"}
        
    encode_list_known_with_ids = [encode_list_known, student_ids]

    file = open("EncodeFile.p", "wb")
    pickle.dump(encode_list_known_with_ids, file)
    file.close()
    
    encodeListKnown = encode_list_known
    studentIds = student_ids
    
    return {"status": "success", "encoded_faces": len(encode_list_known), "total_images": len(img_list)}

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
        
        if existing_img.shape == new_img.shape:
            difference = cv2.norm(existing_img, new_img, cv2.NORM_L2)
            if difference < threshold:
                return True
                
    return False

load_encodings()

@app.post("/detect-face/")
async def detect_face(file: UploadFile = File(...)):
    if not encodeListKnown:
        return {"recognized_person": "No encodings available", "confidence": 0}

    image_bytes = await file.read()
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        return {"recognized_person": "Invalid image", "confidence": 0}

    processed_img = preprocess_image(img)
    
    faceCurFrame = face_recognition.face_locations(
        processed_img, 
        model=FACE_LOCATIONS_MODEL,
        number_of_times_to_upsample=NUMBER_OF_TIMES_TO_UPSAMPLE
    )
    
    if not faceCurFrame:
        return {"recognized_person": "No face detected", "confidence": 0}
    
    largest_face = max(faceCurFrame, key=lambda rect: (rect[2] - rect[0]) * (rect[1] - rect[3]))
    
    encodeCurFrame = face_recognition.face_encodings(
        processed_img, 
        [largest_face], 
        num_jitters=2,
        model=MODEL
    )
    
    if not encodeCurFrame:
        return {"recognized_person": "Failed to encode face", "confidence": 0}

    recognized_person, match_distance = find_best_match(encodeCurFrame[0], encodeListKnown, studentIds)
    
    confidence = max(0, min(100, int((1 - match_distance) * 100)))
    
    if recognized_person == "Unknown" and faceCurFrame:
        try:
            filename = f"unknown_{uuid.uuid4()}.jpg"
            filepath = os.path.join(UNKNOWN_IMAGES_DIR, filename)
            
            cv2.imwrite(filepath, img)
            
            if is_duplicate_image(filepath):
                os.remove(filepath)
            
        except Exception as e:
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except:
                    pass

    return {"recognized_person": recognized_person, "confidence": confidence}

@app.post("/store-member-image/")
async def store_member_image(
    file: UploadFile = File(...), 
    memberId: str = Form(...)
):
    filename = f"{memberId}_{uuid.uuid4()}.jpg"
    member_dir = os.path.join(MEMBER_IMAGES_DIR, str(memberId))
    filepath = os.path.join(member_dir, filename)
    
    os.makedirs(member_dir, exist_ok=True)
    
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {"filename": filename, "status": "success"}

@app.post("/store-unknown-image/")
async def store_unknown_image(file: UploadFile = File(...)):
    filename = f"unknown_{uuid.uuid4()}.jpg"
    filepath = os.path.join(UNKNOWN_IMAGES_DIR, filename)
    
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {"filename": filename, "status": "success"}

@app.get("/get-member-images/{member_id}")
async def get_member_images(member_id: str):
    member_dir = os.path.join(MEMBER_IMAGES_DIR, member_id)
    if not os.path.exists(member_dir):
        return {"images": []}
    
    images = [
        f for f in os.listdir(member_dir) 
        if f.lower().endswith(('.png', '.jpg', '.jpeg'))
    ]
    return {"images": images}

@app.delete("/delete-image/{member_id}/{filename}")
async def delete_image(member_id: str, filename: str):
    filepath = os.path.join(MEMBER_IMAGES_DIR, member_id, filename)
    
    try:
        os.remove(filepath)
        return {"status": "success", "message": "Image deleted"}
    except FileNotFoundError:
        return {"status": "error", "message": "File not found"}

@app.get("/get-unknown-images/")
async def get_unknown_images():
    try:
        if not os.path.exists(UNKNOWN_IMAGES_DIR):
            return {"images": []}
        
        images = [
            f for f in os.listdir(UNKNOWN_IMAGES_DIR) 
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))
        ]
        return {"images": images}
    except Exception as e:
        return {"images": [], "error": str(e)}

@app.get("/get-unknown-image/{filename}")
async def get_unknown_image(filename: str):
    file_path = os.path.join(UNKNOWN_IMAGES_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
    
    return FileResponse(file_path)

@app.delete("/delete-unknown-image/{filename}")
async def delete_unknown_image(filename: str):
    file_path = os.path.join(UNKNOWN_IMAGES_DIR, filename)
    
    try:
        os.remove(file_path)
        return {"status": "success", "message": "Unknown image deleted"}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Image not found")

@app.post("/generate-encodings/")
async def api_generate_encodings():
    return generate_encodings()

@app.post("/add-face-encoding/")
async def add_face_encoding(
    file: UploadFile = File(...),
    person_id: str = Form(...)
):
    global encodeListKnown, studentIds
    
    image_bytes = await file.read()
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        return {"status": "error", "message": "Invalid image"}
    
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
        return {"status": "error", "message": "No face detected in image"}
    
    face_encodings = face_recognition.face_encodings(
        processed_img, 
        face_locations,
        num_jitters=3,
        model=MODEL
    )
    
    if not face_encodings:
        return {"status": "error", "message": "Failed to encode face"}
    
    if person_id in studentIds:
        idx = studentIds.index(person_id)
        encodeListKnown[idx] = face_encodings[0]
    else:
        encodeListKnown.append(face_encodings[0])
        studentIds.append(person_id)
    
    encode_list_known_with_ids = [encodeListKnown, studentIds]
    with open("EncodeFile.p", "wb") as file:
        pickle.dump(encode_list_known_with_ids, file)
    
    return {"status": "success", "message": f"Added encoding for {person_id}"}

@app.get("/list-encoded-faces/")
async def list_encoded_faces():
    return {"faces": studentIds, "count": len(studentIds)}

@app.get("/health/")
async def health_check():
    return {"status": "Service is running", "encoded_faces": len(encodeListKnown)}

if __name__ == '__main__':
    if not os.path.exists("EncodeFile.p"):
        generate_encodings()
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
