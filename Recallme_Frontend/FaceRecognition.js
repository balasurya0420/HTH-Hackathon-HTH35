import React, { useRef, useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Webcam from "react-webcam";
import axios from "axios";
import { FaCamera, FaUpload, FaUser, FaCircleNotch } from "react-icons/fa";
import { HiOutlineLightBulb } from "react-icons/hi";

const FaceRecognition = () => {
    const webcamRef = useRef(null);
    const fileInputRef = useRef(null);
    const [recognizedPerson, setRecognizedPerson] = useState("No one detected");
    const [isProcessing, setIsProcessing] = useState(false);
    const [cameraError, setCameraError] = useState(false);
    const [showAnimation, setShowAnimation] = useState(false);
    const [isCameraActive, setIsCameraActive] = useState(true);
    const navigate = useNavigate();

    // Video constraints for better webcam performance
    const videoConstraints = {
        width: 640,
        height: 480,
        facingMode: "user"
    };

    useEffect(() => {
        // When component mounts, ensure camera is set to active
        setIsCameraActive(true);
        
        return () => {
            // When component unmounts, set camera to inactive and stop all tracks
            setIsCameraActive(false);
            if (webcamRef.current && webcamRef.current.video && webcamRef.current.video.srcObject) {
                const tracks = webcamRef.current.video.srcObject.getTracks();
                tracks.forEach(track => track.stop());
            }
        };
    }, []);

    const handleUserMedia = (stream) => {
        console.log("Webcam connected successfully");
    };

    const handleUserMediaError = (error) => {
        console.error("Webcam Error:", error);
        setCameraError(true);
    };

    const processImage = async (imageFile) => {
        setIsProcessing(true);
        setShowAnimation(true);
        const formData = new FormData();
        formData.append("file", imageFile, "image.jpg");

        try {
            const response = await axios.post("http://127.0.0.1:8000/detect-face/", formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            
            const recognizedId = response.data.recognized_person;
            setRecognizedPerson(recognizedId);

            // Store image based on recognition
            if (recognizedId !== "Unknown") {
                await storeRecognizedImage(imageFile, recognizedId);
                setTimeout(() => {
                    setIsCameraActive(false);
                    navigate(`/${recognizedId}`);
                }, 1500); // Delay navigation to show the recognition result
            } else {
                await storeUnknownImage(imageFile);
            }
        } catch (error) {
            console.error("Error detecting face:", error);
            setRecognizedPerson("Error detecting face");
        } finally {
            setIsProcessing(false);
            setTimeout(() => {
                setShowAnimation(false);
            }, 2000);
        }
    };

    const storeRecognizedImage = async (imageFile, memberId) => {
        const formData = new FormData();
        formData.append("file", imageFile);
        formData.append("memberId", memberId);

        try {
            await axios.post("http://127.0.0.1:8000/store-member-image/", formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
        } catch (error) {
            console.error("Error storing member image:", error);
        }
    };

    const storeUnknownImage = async (imageFile) => {
        const formData = new FormData();
        formData.append("file", imageFile);

        try {
            await axios.post("http://127.0.0.1:8000/store-unknown-image/", formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
        } catch (error) {
            console.error("Error storing unknown image:", error);
        }
    };

    const capture = async () => {
        if (webcamRef.current) {
            console.log("Attempting to capture image...");
            const imageSrc = webcamRef.current.getScreenshot();
            if (imageSrc) {
                console.log("Image captured successfully");
                const blob = await fetch(imageSrc).then((res) => res.blob());
                await processImage(blob);
            } else {
                console.error("Failed to capture image - no screenshot data");
                setCameraError(true);
            }
        } else {
            console.error("Webcam reference is not available");
            setCameraError(true);
        }
    };

    const handleFileUpload = async (event) => {
        const file = event.target.files[0];
        if (file) {
            await processImage(file);
        }
    };

    return (
        <div className="face-recognition-container">
            <div className="content-wrapper">
                <header className="recognition-header">
                    <h1>Smart Face Recognition</h1>
                    <p className="subtitle">
                        <HiOutlineLightBulb className="tip-icon" />
                        Position your face in the frame or upload an image
                    </p>
                </header>
                
                <div className="camera-container">
                    {cameraError ? (
                        <div className="camera-error">
                            <FaUser className="camera-error-icon" />
                            <p>Camera access denied or unavailable</p>
                            <button className="retry-camera" onClick={() => setCameraError(false)}>
                                Try Again
                            </button>
                        </div>
                    ) : isCameraActive ? (
                        <Webcam 
                            audio={false}
                            ref={webcamRef} 
                            screenshotFormat="image/jpeg"
                            videoConstraints={videoConstraints}
                            className="webcam-preview"
                            mirrored={true}
                            onUserMedia={handleUserMedia}
                            onUserMediaError={handleUserMediaError}
                        />
                    ) : (
                        <div className="camera-offline">
                            <p>Camera is turned off</p>
                        </div>
                    )}
                    
                    {showAnimation && (
                        <div className={`recognition-overlay ${recognizedPerson !== "Unknown" && recognizedPerson !== "No one detected" ? "success" : recognizedPerson === "Unknown" ? "unknown" : ""}`}>
                            {isProcessing ? (
                                <div className="scanning-animation">
                                    <div className="scanning-line"></div>
                                </div>
                            ) : (
                                <div className="recognition-result">
                                    {recognizedPerson !== "Unknown" && recognizedPerson !== "No one detected" ? (
                                        <>
                                            <div className="recognition-icon success">✓</div>
                                            <p>Welcome, {recognizedPerson}!</p>
                                        </>
                                    ) : recognizedPerson === "Unknown" ? (
                                        <>
                                            <div className="recognition-icon unknown">?</div>
                                            <p>Face not recognized</p>
                                        </>
                                    ) : (
                                        <>
                                            <div className="recognition-icon error">!</div>
                                            <p>Error detecting face</p>
                                        </>
                                    )}
                                </div>
                            )}
                        </div>
                    )}
                </div>
                
                <div className="action-buttons">
                    <button
                        onClick={capture}
                        className="action-button capture-button"
                        disabled={isProcessing || cameraError || !isCameraActive}
                    >
                        {isProcessing ? <FaCircleNotch className="spinning" /> : <FaCamera />}
                        <span>Capture</span>
                    </button>
                    
                    <input 
                        type="file" 
                        ref={fileInputRef} 
                        className="file-input" 
                        accept="image/*"
                        onChange={handleFileUpload}
                    />
                    
                    <button
                        onClick={() => fileInputRef.current.click()}
                        className="action-button upload-button"
                        disabled={isProcessing}
                    >
                        {isProcessing ? <FaCircleNotch className="spinning" /> : <FaUpload />}
                        <span>Upload Image</span>
                    </button>
                </div>
                
                <div className={`recognition-status ${recognizedPerson !== "No one detected" ? "active" : ""}`}>
                    <div className="status-indicator"></div>
                    <p>{recognizedPerson !== "No one detected" ? 
                        `Recognized: ${recognizedPerson}` : 
                        "Ready to recognize"}
                    </p>
                </div>

                {/* Debug info - can be removed in production */}
                <div className="debug-info">
                    <p>Camera Active: {isCameraActive ? "Yes" : "No"}</p>
                    <p>Camera Error: {cameraError ? "Yes" : "No"}</p>
                    <button onClick={() => {
                        setIsCameraActive(!isCameraActive);
                    }} className="debug-button">
                        Toggle Camera
                    </button>
                </div>
            </div>
            
            <style jsx>{`
                .face-recognition-container {
                    max-width: 100%;
                    min-height: 100vh;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    background: linear-gradient(135deg, #e0f7fa 0%, #f5f5f5 100%);
                    padding: 20px;
                    font-family: 'Poppins', -apple-system, BlinkMacSystemFont, sans-serif;
                }
                
                .content-wrapper {
                    width: 100%;
                    max-width: 800px;
                    background: rgba(255, 255, 255, 0.9);
                    border-radius: 24px;
                    box-shadow: 0 10px 40px rgba(0, 150, 255, 0.08), 
                                0 0 20px rgba(0, 150, 255, 0.05);
                    padding: 40px;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    position: relative;
                    overflow: hidden;
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255, 255, 255, 0.7);
                }
                
                .recognition-header {
                    text-align: center;
                    margin-bottom: 24px;
                    width: 100%;
                }
                
                .recognition-header h1 {
                    font-size: 32px;
                    font-weight: 700;
                    margin: 0 0 12px 0;
                    background: linear-gradient(90deg, #4fc3f7, #81d4fa);
                    -webkit-background-clip: text;
                    background-clip: text;
                    -webkit-text-fill-color: transparent;
                    letter-spacing: -0.5px;
                }
                
                .subtitle {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #78909c;
                    font-size: 16px;
                    margin: 0;
                }
                
                .tip-icon {
                    margin-right: 8px;
                    color: #4fc3f7;
                    font-size: 20px;
                }
                
                .camera-container {
                    width: 100%;
                    height: 450px;
                    margin-bottom: 32px;
                    border-radius: 20px;
                    overflow: hidden;
                    position: relative;
                    background-color: #e3f2fd;
                    box-shadow: 0 8px 20px rgba(0, 150, 255, 0.1);
                    border: 3px solid #f5f5f5;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                
                .webcam-preview {
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                    border-radius: 16px;
                }
                
                .camera-error, .camera-offline {
                    width: 100%;
                    height: 100%;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    color: #78909c;
                    background-color: #e3f2fd;
                    border-radius: 16px;
                    text-align: center;
                    padding: 20px;
                }
                
                .camera-error-icon {
                    font-size: 60px;
                    margin-bottom: 20px;
                    color: #b3e5fc;
                }
                
                .retry-camera {
                    margin-top: 15px;
                    padding: 8px 16px;
                    background-color: #4fc3f7;
                    color: white;
                    border: none;
                    border-radius: 20px;
                    cursor: pointer;
                    font-weight: 600;
                    transition: all 0.2s ease;
                }
                
                .retry-camera:hover {
                    background-color: #29b6f6;
                    transform: translateY(-2px);
                }
                
                .recognition-overlay {
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background-color: rgba(0, 0, 0, 0.3);
                    border-radius: 16px;
                    z-index: 2;
                    backdrop-filter: blur(3px);
                    transition: all 0.3s ease;
                }
                
                .recognition-overlay.success {
                    background-color: rgba(77, 208, 225, 0.4);
                }
                
                .recognition-overlay.unknown {
                    background-color: rgba(255, 193, 7, 0.4);
                }
                
                .scanning-animation {
                    width: 100%;
                    height: 100%;
                    position: relative;
                    overflow: hidden;
                }
                
                .scanning-line {
                    position: absolute;
                    width: 100%;
                    height: 4px;
                    background: linear-gradient(90deg, 
                        rgba(255,255,255,0) 0%, 
                        rgba(129,212,250,1) 50%, 
                        rgba(255,255,255,0) 100%);
                    animation: scan 1.8s ease-in-out infinite;
                    box-shadow: 0 0 15px rgba(77, 208, 225, 0.8);
                }
                
                @keyframes scan {
                    0% { top: 0; }
                    50% { top: 100%; }
                    100% { top: 0; }
                }
                
                .recognition-result {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-size: 24px;
                    font-weight: 600;
                    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
                }
                
                .recognition-icon {
                    width: 70px;
                    height: 70px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 30px;
                    margin-bottom: 20px;
                    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.15);
                }
                
                .recognition-icon.success {
                    background-color: #4dd0e1;
                }
                
                .recognition-icon.unknown {
                    background-color: #ffc107;
                }
                
                .recognition-icon.error {
                    background-color: #ff5252;
                }
                
                .action-buttons {
                    display: flex;
                    gap: 20px;
                    margin-bottom: 30px;
                    width: 100%;
                }
                
                .action-button {
                    flex: 1;
                    padding: 16px 24px;
                    border-radius: 16px;
                    border: none;
                    font-size: 17px;
                    font-weight: 600;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 12px;
                    transition: all 0.3s ease;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
                }
                
                .action-button:disabled {
                    opacity: 0.7;
                    cursor: not-allowed;
                }
                
                .capture-button {
                    background: linear-gradient(45deg, #ff56b1, #f06292);
                    color: white;
                }
                
                .capture-button:hover:not(:disabled) {
                    background: linear-gradient(45deg, #f06292, #ec407a);
                    transform: translateY(-3px);
                    box-shadow: 0 6px 15px rgba(240, 98, 146, 0.4);
                }
                
                .upload-button {
                    background: linear-gradient(45deg, #4fc3f7, #29b6f6);
                    color: white;
                }
                
                .upload-button:hover:not(:disabled) {
                    background: linear-gradient(45deg, #29b6f6, #03a9f4);
                    transform: translateY(-3px);
                    box-shadow: 0 6px 15px rgba(41, 182, 246, 0.4);
                }
                
                .file-input {
                    display: none;
                }
                
                .recognition-status {
                    display: flex;
                    align-items: center;
                    padding: 14px 20px;
                    border-radius: 16px;
                    background-color: #f5f5f5;
                    width: 100%;
                    transition: all 0.3s ease;
                }
                
                .recognition-status.active {
                    background-color: #e1f5fe;
                }
                
                .status-indicator {
                    width: 12px;
                    height: 12px;
                    border-radius: 50%;
                    background-color: #b0bec5;
                    margin-right: 14px;
                    transition: all 0.3s ease;
                }
                
                .recognition-status.active .status-indicator {
                    background-color: #29b6f6;
                    box-shadow: 0 0 0 4px rgba(41, 182, 246, 0.2);
                }
                
                .recognition-status p {
                    margin: 0;
                    color: #78909c;
                    font-size: 15px;
                    font-weight: 500;
                    transition: all 0.3s ease;
                }
                
                .recognition-status.active p {
                    color: #0277bd;
                    font-weight: 600;
                }
                
                .spinning {
                    animation: spin 1s linear infinite;
                }
                
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                
                .debug-info {
                    margin-top: 20px;
                    padding: 15px;
                    background-color: #f5f5f5;
                    border-radius: 10px;
                    width: 100%;
                    font-size: 14px;
                }
                
                .debug-button {
                    background-color: #90caf9;
                    border: none;
                    padding: 5px 10px;
                    border-radius: 5px;
                    cursor: pointer;
                    margin-top: 10px;
                }
                
                @media (max-width: 768px) {
                    .content-wrapper {
                        padding: 30px 20px;
                        border-radius: 20px;
                    }
                    
                    .camera-container {
                        height: 350px;
                    }
                }
                
                @media (max-width: 500px) {
                    .content-wrapper {
                        padding: 20px 15px;
                    }
                    
                    .camera-container {
                        height: 300px;
                    }
                    
                    .action-buttons {
                        flex-direction: column;
                    }
                    
                    .action-button {
                        width: 100%;
                    }
                    
                    .recognition-header h1 {
                        font-size: 28px;
                    }
                }
            `}</style>
        </div>
    );
};

export default FaceRecognition;