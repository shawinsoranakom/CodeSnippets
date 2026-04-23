def main():
    """Ultralytics YOLO26 Pose Estimation + Tracking example."""
    parser = argparse.ArgumentParser(description="Ultralytics YOLO26 Pose Estimation + Tracking - Axelera Voyager SDK")
    parser.add_argument("--model", type=str, required=True, help="Path to compiled .axm model")
    parser.add_argument("--source", type=str, default="0", help="Image, video path, or camera index")
    parser.add_argument("--conf", type=float, default=0.25, help="Confidence threshold")
    parser.add_argument(
        "--tracker",
        type=str,
        default="tracktrack",
        choices=["bytetrack", "oc-sort", "sort", "tracktrack", "none"],
        help="Tracking algorithm (use 'none' to disable tracking)",
    )
    parser.add_argument(
        "--no-display", action="store_true", help="Disable GUI window (headless mode, saves to --output)"
    )
    parser.add_argument("--output", type=str, default="output.mp4", help="Output video path when --no-display is set")
    args = parser.parse_args()

    tracker_algo = None if args.tracker == "none" else args.tracker
    pipeline = build_pipeline(args.model, args.conf, tracker_algo)
    use_tracking = tracker_algo is not None

    source = int(args.source) if args.source.isdigit() else args.source
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open source: {args.source}")

    writer = None
    frame_count = 0
    frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    is_image = frames == 1

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = pipeline(frame)
        annotated = draw_tracked_poses(frame, results) if use_tracking else draw_pose(frame, results, args.conf)
        frame_count += 1

        if args.no_display:
            if writer is None:
                h, w = annotated.shape[:2]
                fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
                writer = cv2.VideoWriter(args.output, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
            writer.write(annotated)
            if frame_count % 100 == 0:
                print(f"  frame {frame_count}: {len(results)} {'tracks' if use_tracking else 'detections'}")
        else:
            title = "Ultralytics YOLO26 Pose Tracking" if use_tracking else "Ultralytics YOLO26 Pose"
            cv2.imshow(title, annotated)
            if cv2.waitKey(0 if is_image else 1) & 0xFF in [ord("q"), ord("Q"), 27]:
                break

    cap.release()
    if writer is not None:
        writer.release()
        print(f"Saved {frame_count} frames to {args.output}")
    else:
        cv2.destroyAllWindows()