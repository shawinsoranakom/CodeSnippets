def test_labels_and_crops():
    """Test output from prediction args for saving YOLO detection labels and crops."""
    imgs = [SOURCE, ASSETS / "zidane.jpg"]
    results = YOLO(WEIGHTS_DIR / "yolo26n.pt")(imgs, imgsz=320, save_txt=True, save_crop=True)
    save_path = Path(results[0].save_dir)
    for r in results:
        im_name = Path(r.path).stem
        cls_idxs = r.boxes.cls.int().tolist()
        # Check that detections are made (at least 2 detections per image expected)
        assert len(cls_idxs) >= 2, f"Expected at least 2 detections, got {len(cls_idxs)}"
        # Check label path
        labels = save_path / f"labels/{im_name}.txt"
        assert labels.exists(), f"Label file {labels} does not exist"
        # Check detections match label count
        label_count = len([line for line in labels.read_text().splitlines() if line])
        assert len(r.boxes.data) == label_count, f"Box count {len(r.boxes.data)} != label count {label_count}"
        # Check crops path and files
        crop_dirs = list((save_path / "crops").iterdir())
        crop_files = [f for p in crop_dirs for f in p.glob("*")]
        # Crop directories match detections
        crop_dir_names = {d.name for d in crop_dirs}
        assert all(r.names.get(c) in crop_dir_names for c in cls_idxs), (
            f"Crop dirs {crop_dir_names} don't match classes {cls_idxs}"
        )
        # Same number of crops as detections
        crop_count = len([f for f in crop_files if im_name in f.name])
        assert crop_count == len(r.boxes.data), f"Crop count {crop_count} != detection count {len(r.boxes.data)}"