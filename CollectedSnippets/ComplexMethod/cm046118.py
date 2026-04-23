def test_predict_multiple_devices():
    """Validate model prediction consistency across CPU and CUDA devices."""
    model = YOLO("yolo26n.pt")

    # Test CPU
    model = model.cpu()
    assert str(model.device) == "cpu"
    _ = model(SOURCE)
    assert str(model.device) == "cpu"

    # Test CUDA
    cuda_device = f"cuda:{DEVICES[0]}"
    model = model.to(cuda_device)
    assert str(model.device) == cuda_device
    _ = model(SOURCE)
    assert str(model.device) == cuda_device

    # Test CPU again
    model = model.cpu()
    assert str(model.device) == "cpu"
    _ = model(SOURCE)
    assert str(model.device) == "cpu"

    # Test CUDA again
    model = model.to(cuda_device)
    assert str(model.device) == cuda_device
    _ = model(SOURCE)
    assert str(model.device) == cuda_device