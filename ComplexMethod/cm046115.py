def test_predict_all_image_formats():
    """Predict on all 12 image formats (AVIF, BMP, DNG, HEIC, JP2, JPEG, JPG, MPO, PNG, TIF, TIFF, WebP)."""
    # Download dataset if needed
    data = check_det_dataset("coco12-formats.yaml")
    dataset_path = Path(data["path"])

    # Collect all images from train and val
    expected = {"avif", "bmp", "dng", "heic", "jp2", "jpeg", "jpg", "mpo", "png", "tif", "tiff", "webp"}
    images = [im for im in (dataset_path / "images" / "train").glob("*.*") if im.suffix.lower().lstrip(".") in expected]
    images += [im for im in (dataset_path / "images" / "val").glob("*.*") if im.suffix.lower().lstrip(".") in expected]
    assert len(images) == 12, f"Expected 12 images, found {len(images)}"

    # Verify all format extensions are represented
    extensions = {img.suffix.lower().lstrip(".") for img in images}
    assert extensions == expected, f"Missing formats: {expected - extensions}"

    # Run inference on all images
    model = YOLO(MODEL)
    results = model(images, imgsz=32)
    assert len(results) == 12, f"Expected 12 results, got {len(results)}"