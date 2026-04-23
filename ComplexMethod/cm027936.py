def analyze_facial_expressions(video_path: str) -> dict:
    """
    Analyzes facial expressions in a video to detect emotions and engagement.

    Args:
        video_path: The path to the video file.

    Returns:
        A dictionary containing the emotion timeline and engagement metrics.
    """
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1)
    cap = cv2.VideoCapture(video_path)

    emotion_timeline = []
    eye_contact_count = 0
    smile_count = 0
    frame_count = 0
    fps = cap.get(cv2.CAP_PROP_FPS)

    # Process every nth frame for performance optimization
    frame_interval = 5

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        if frame_count % frame_interval != 0:
            continue

        # Resize frame for faster processing
        frame = cv2.resize(frame, (640, 480))
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb_frame)

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                # Extract landmarks
                landmarks = face_landmarks.landmark

                # Convert landmarks to pixel coordinates
                h, w, _ = frame.shape
                landmark_coords = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks]

                # Emotion Detection using DeepFace & Smile Detection
                try:
                    analysis = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
                    emotion = analysis[0]['dominant_emotion']
                    if emotion == "happy":
                        smile_count += 1

                    timestamp = frame_count / fps
                    # convert timestamp into seconds
                    timestamp = round(timestamp, 2)
                    emotion_timeline.append({"timestamp": timestamp, "emotion": emotion})
                except Exception as e:
                    print(f"Error analyzing frame: {e}")
                    continue

                # Engagement Metric: Eye contact estimation
                # Using eye landmarks: 159 (left eye upper lid), 145 (left eye lower lid), 386 (right eye upper lid), 374 (right eye lower lid)
                left_eye_upper_lid = landmark_coords[159]
                left_eye_lower_lid = landmark_coords[145]
                right_eye_upper_lid = landmark_coords[386]
                right_eye_lower_lid = landmark_coords[374]

                left_eye_opening = np.linalg.norm(np.array(left_eye_upper_lid) - np.array(left_eye_lower_lid))
                right_eye_opening = np.linalg.norm(np.array(right_eye_upper_lid) - np.array(right_eye_lower_lid))

                eye_opening_avg = (left_eye_opening + right_eye_opening) / 2

                # Simple heuristic: if eyes are wide open, assume eye contact
                if eye_opening_avg > 5:  # Threshold adjustment through experimentation
                    eye_contact_count += 1

    cap.release()
    face_mesh.close()

    total_processed_frames = frame_count // frame_interval
    if total_processed_frames == 0:
        total_processed_frames = 1  # Avoid division by zero

    return json.dumps({
        "emotion_timeline": emotion_timeline,
        "engagement_metrics": {
            "eye_contact_frequency": eye_contact_count / total_processed_frames,
            "smile_frequency": smile_count / total_processed_frames
        }
    })