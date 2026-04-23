def test_predict_img(model_name):
    """Test YOLO model predictions on various image input types and sources, including online images."""
    channels = 1 if model_name == "yolo11n-grayscale.pt" else 3
    model = YOLO(WEIGHTS_DIR / model_name)
    im = cv2.imread(str(SOURCE), flags=cv2.IMREAD_GRAYSCALE if channels == 1 else cv2.IMREAD_COLOR)  # uint8 NumPy array
    assert len(model(source=Image.open(SOURCE), save=True, verbose=True, imgsz=32)) == 1  # PIL
    assert len(model(source=im, save=True, save_txt=True, imgsz=32)) == 1  # ndarray
    assert len(model(torch.rand((2, channels, 32, 32)), imgsz=32)) == 2  # batch-size 2 Tensor, FP32 0.0-1.0 RGB order
    assert len(model(source=[im, im], save=True, save_txt=True, imgsz=32)) == 2  # batch
    assert len(list(model(source=[im, im], save=True, stream=True, imgsz=32))) == 2  # stream
    assert len(model(torch.zeros(320, 640, channels).numpy().astype(np.uint8), imgsz=32)) == 1  # tensor to numpy
    batch = [
        str(SOURCE),  # filename
        Path(SOURCE),  # Path
        "https://cdn.jsdelivr.net/gh/ultralytics/assets@main/im/zidane.jpg?token=123" if ONLINE else SOURCE,  # URI
        im,  # OpenCV
        Image.open(SOURCE),  # PIL
        np.zeros((320, 640, channels), dtype=np.uint8),  # numpy
    ]
    assert len(model(batch, imgsz=32, classes=0)) == len(batch)