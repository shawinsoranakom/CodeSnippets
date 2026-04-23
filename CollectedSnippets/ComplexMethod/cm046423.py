def run(
    weights: str = "yolo11n.pt",
    device: str = "",
    source: str = "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    output_path: str | None = None,
    crop_margin_percentage: int = 10,
    num_video_sequence_samples: int = 8,
    skip_frame: int = 2,
    video_cls_overlap_ratio: float = 0.25,
    fp16: bool = False,
    video_classifier_model: str = "microsoft/xclip-base-patch32",
    labels: list[str] | None = None,
) -> None:
    """Run action recognition on a video source using YOLO for object detection and a video classifier.

    Args:
        weights (str): Path to the YOLO model weights.
        device (str): Device to run the model on. Use 'cuda' for NVIDIA GPU, 'mps' for Apple Silicon, or 'cpu'.
        source (str): Path to mp4 video file or YouTube URL.
        output_path (str, optional): Path to save the output video.
        crop_margin_percentage (int): Percentage of margin to add around detected objects.
        num_video_sequence_samples (int): Number of video frames to use for classification.
        skip_frame (int): Number of frames to skip between detections.
        video_cls_overlap_ratio (float): Overlap ratio between video sequences.
        fp16 (bool): Whether to use half-precision floating point.
        video_classifier_model (str): Name or path of the video classifier model.
        labels (list[str], optional): List of labels for zero-shot classification.
    """
    if labels is None:
        labels = [
            "walking",
            "running",
            "brushing teeth",
            "looking into phone",
            "weight lifting",
            "cooking",
            "sitting",
        ]
    # Initialize models and device
    device = select_device(device)
    yolo_model = YOLO(weights).to(device)
    if video_classifier_model in TorchVisionVideoClassifier.available_model_names():
        print("'fp16' is not supported for TorchVisionVideoClassifier. Setting fp16 to False.")
        print(
            "'labels' is not used for TorchVisionVideoClassifier. Ignoring the provided labels and using Kinetics-400 labels."
        )
        video_classifier = TorchVisionVideoClassifier(video_classifier_model, device=device)
    else:
        video_classifier = HuggingFaceVideoClassifier(
            labels, model_name=video_classifier_model, device=device, fp16=fp16
        )

    # Initialize video capture
    if source.startswith("http") and urlparse(source).hostname in {"www.youtube.com", "youtube.com", "youtu.be"}:
        source = get_best_youtube_url(source)
    elif not source.endswith(".mp4"):
        raise ValueError("Invalid source. Supported sources are YouTube URLs and MP4 files.")
    cap = cv2.VideoCapture(source)

    # Get video properties
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    # Initialize VideoWriter
    if output_path is not None:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))

    # Initialize track history
    track_history = defaultdict(list)
    frame_counter = 0

    track_ids_to_infer = []
    crops_to_infer = []
    pred_labels = []
    pred_confs = []

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        frame_counter += 1

        # Run YOLO tracking
        results = yolo_model.track(frame, persist=True, classes=[0])  # Track only person class

        if results[0].boxes.is_track:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            track_ids = results[0].boxes.id.cpu().numpy()

            # Visualize prediction
            annotator = Annotator(frame, line_width=3, font_size=10, pil=False)

            if frame_counter % skip_frame == 0:
                crops_to_infer = []
                track_ids_to_infer = []

            for box, track_id in zip(boxes, track_ids):
                if frame_counter % skip_frame == 0:
                    crop = crop_and_pad(frame, box, crop_margin_percentage)
                    track_history[track_id].append(crop)

                if len(track_history[track_id]) > num_video_sequence_samples:
                    track_history[track_id].pop(0)

                if len(track_history[track_id]) == num_video_sequence_samples and frame_counter % skip_frame == 0:
                    start_time = time.time()
                    crops = video_classifier.preprocess_crops_for_video_cls(track_history[track_id])
                    end_time = time.time()
                    preprocess_time = end_time - start_time
                    print(f"video cls preprocess time: {preprocess_time:.4f} seconds")
                    crops_to_infer.append(crops)
                    track_ids_to_infer.append(track_id)

            if crops_to_infer and (
                not pred_labels
                or frame_counter % int(num_video_sequence_samples * skip_frame * (1 - video_cls_overlap_ratio)) == 0
            ):
                crops_batch = torch.cat(crops_to_infer, dim=0)

                start_inference_time = time.time()
                output_batch = video_classifier(crops_batch)
                end_inference_time = time.time()
                inference_time = end_inference_time - start_inference_time
                print(f"video cls inference time: {inference_time:.4f} seconds")

                pred_labels, pred_confs = video_classifier.postprocess(output_batch)

            if track_ids_to_infer and crops_to_infer:
                for box, track_id, pred_label, pred_conf in zip(boxes, track_ids_to_infer, pred_labels, pred_confs):
                    top2_preds = sorted(zip(pred_label, pred_conf), key=lambda x: x[1], reverse=True)
                    label_text = " | ".join([f"{label} ({conf:.2f})" for label, conf in top2_preds])
                    annotator.box_label(box, label_text, color=(0, 0, 255))

        # Write the annotated frame to the output video
        if output_path is not None:
            out.write(frame)

        # Display the annotated frame
        cv2.imshow("YOLOv8 Tracking with S3D Classification", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    if output_path is not None:
        out.release()
    cv2.destroyAllWindows()