def inference(
        self,
        weights: str = "yolo11n.pt",
        source: str = "test.mp4",
        view_img: bool = False,
        save_img: bool = False,
        exist_ok: bool = False,
        device: str = "",
        hide_conf: bool = False,
        slice_width: int = 512,
        slice_height: int = 512,
    ) -> None:
        """Run object detection on a video using YOLO11 and SAHI.

        The function processes each frame of the video, applies sliced inference using SAHI, and optionally displays
        and/or saves the results with bounding boxes and labels.

        Args:
            weights (str): Model weights' path.
            source (str): Video file path.
            view_img (bool): Whether to display results in a window.
            save_img (bool): Whether to save results to a video file.
            exist_ok (bool): Whether to overwrite existing output files.
            device (str, optional): CUDA device, i.e., '0' or '0,1,2,3' or 'cpu'.
            hide_conf (bool, optional): Whether to hide confidence scores in the output.
            slice_width (int, optional): Slice width for inference.
            slice_height (int, optional): Slice height for inference.
        """
        # Video setup
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            raise FileNotFoundError(f"Unable to open video source: '{source}'")

        save_dir = None
        if save_img:
            save_dir = increment_path("runs/detect/predict", exist_ok)
            save_dir.mkdir(parents=True, exist_ok=True)

        # Load model
        self.load_model(weights, device)
        idx = 0  # Index for image frame writing
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break

            # Perform sliced prediction using SAHI
            results = get_sliced_prediction(
                frame[..., ::-1],  # Convert BGR to RGB
                self.detection_model,
                slice_height=slice_height,
                slice_width=slice_width,
            )

            # Display results if requested
            if view_img:
                cv2.imshow("Ultralytics YOLO Inference", frame)

            # Save results if requested
            if save_img and save_dir is not None:
                idx += 1
                results.export_visuals(export_dir=save_dir, file_name=f"img_{idx}", hide_conf=hide_conf)

            # Break loop if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        # Clean up resources
        cap.release()
        cv2.destroyAllWindows()