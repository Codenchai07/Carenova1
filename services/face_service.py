from deepface import DeepFace
import cv2
import numpy as np
import base64

def extract_embedding(base64_image):
    """
    Convert base64 image → OpenCV format → DeepFace embedding
    """
    try:
        img_data = base64.b64decode(base64_image.split(',')[1])
        np_img = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

        # Extract face embedding
        embedding_result = DeepFace.represent(img, model_name="Facenet")
        embedding = embedding_result[0]["embedding"]
        return embedding

    except Exception as e:
        print("Embedding error:", e)
        return None
