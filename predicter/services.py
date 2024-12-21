import cv2
import numpy as np
import tensorflow as tf
import os

IMAGE_HEIGHT, IMAGE_WIDTH = 64, 64
SEQUENCE_LENGTH = 16
CLASSES_LIST = ["NonViolence", "Violence"]

model = tf.keras.models.load_model('violence_detection_model.keras')


def frames_extraction(video_path):
    frames_list = []
    video_reader = cv2.VideoCapture(video_path)

    if not video_reader.isOpened():
        raise ValueError(f"Error: Could not open video file {video_path}")

    video_frames_count = int(video_reader.get(cv2.CAP_PROP_FRAME_COUNT))
    skip_frames_window = max(1, video_frames_count // SEQUENCE_LENGTH)

    for frame_counter in range(SEQUENCE_LENGTH):
        video_reader.set(cv2.CAP_PROP_POS_FRAMES, frame_counter * skip_frames_window)
        success, frame = video_reader.read()
        if not success:
            break
        frame = cv2.resize(frame, (IMAGE_HEIGHT, IMAGE_WIDTH))
        frame = frame / 255.0
        frames_list.append(frame)

    video_reader.release()

    if len(frames_list) != SEQUENCE_LENGTH:
        raise ValueError("Error: Video does not contain enough frames for prediction.")

    return frames_list


def predict_video_class(video_path):
    try:
        frames = frames_extraction(video_path)
        frames_array = np.expand_dims(frames, axis=0)
        predictions = model.predict(frames_array)[0]

        result = {}
        for i, class_name in enumerate(CLASSES_LIST):
            result[class_name] = f"{predictions[i] * 100:.2f}%"

        predicted_class = np.argmax(predictions)
        predicted_label = CLASSES_LIST[predicted_class]
        confidence = predictions[predicted_class] * 100

        return {
            "predicted_class": predicted_label,
            "confidence": f"{confidence:.2f}%",
            "class_probabilities": result
        }

    except Exception as e:
        return {"error": str(e)}


def predict_video(video_path):
    if not os.path.isfile(video_path):
        return {"error": f"File {video_path} does not exist"}

    return predict_video_class(video_path)
