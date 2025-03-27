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
from typing import Optional
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

def find_encodings(img_list):
    encode_list = []
    for img in img_list:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        try:
            face_encodings = face_recognition.face_encodings(img)
            if face_encodings:
                encode = face_encodings[0]
                encode_list.append(encode)
        except Exception as e:
            continue
    return encode_list

def generate_encodings():
    global encodeListKnown, studentIds
    folder_path = IMAGES_DIR
    path_list = os.listdir(folder_path)
    img_list = []
    student_ids = []
    for path in path_list:
        if path.lower().endswith(('.png', '.jpg', '.jpeg')):
            img_list.append(cv2.imread(os.path.join(folder_path, path)))
            student_ids.append(os.path.splitext(path)[0])
    encode_list_known = find_encodings(img_list)
    encode_list_known_with_ids = [encode_list_known, student_ids]
    file = open("EncodeFile.p", "wb")
    pickle.dump(encode_list_known_with_ids, file)
    file.close()
    encodeListKnown = encode_list_known
    studentIds = student_ids
    return {"status": "success", "encoded_faces": len(encode_list_known)}

load_encodings()

def is_duplicate_image(new_img_path):
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
            if difference < 100:
                return True
    return False

@app.post("/detect-face/")
async def detect_face(file: UploadFile = File(...)):
    if not encodeListKnown:
        return {"recognized_person": "No encodings available"}
    image_bytes = await file.read()
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)
    faceCurFrame = face_recognition.face_locations(imgS)
    encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)
    result = "Unknown"
    for encodeFace in encodeCurFrame:
        try:
            matches = face_recognition.compare_faces(encodeListKnown, encodeFace, tolerance=0.6)
            if True in matches:
                matchIndex = matches.index(True)
                result = studentIds[matchIndex]
                break
        except Exception as e:
            continue
    if result == "Unknown" and faceCurFrame:
        try:
            filename = f"unknown_{uuid.uuid4()}.jpg"
            filepath = os.path.join(UNKNOWN_IMAGES_DIR, filename)
            cv2.imwrite(filepath, img)
            if is_duplicate_image(filepath):
                os.remove(filepath)
            else:
                pass
        except Exception as e:
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except:
                    pass
    return {"recognized_person": result}

@app.post("/store-member-image/")
async def store_member_image(
    file: UploadFile = File(...), 
    memberId: str = Form(...)
):
    filename = f"{memberId}_{uuid.uuid4()}.jpg"
    filepath = os.path.join(MEMBER_IMAGES_DIR, str(memberId), filename)
    os.makedirs(os.path.join(MEMBER_IMAGES_DIR, str(memberId)), exist_ok=True)
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
        if f.endswith(('.png', '.jpg', '.jpeg'))
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

@app.get("/health/")
async def health_check():
    return {"status": "Service is running"}

if __name__ == '__main__':
    if not os.path.exists("EncodeFile.p"):
        generate_encodings()
    uvicorn.run(app, host="0.0.0.0", port=8000)
