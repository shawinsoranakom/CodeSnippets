def run(
    weights=ROOT / "yolov5s.pt",  # weights path
    imgsz=640,  # inference size (pixels)
    batch_size=1,  # batch size
    data=ROOT / "data/coco128.yaml",  # dataset.yaml path
    device="",  # cuda device, i.e. 0 or 0,1,2,3 or cpu
    half=False,  # use FP16 half-precision inference
    test=False,  # test exports only
    pt_only=False,  # test PyTorch only
    hard_fail=False,  # throw error on benchmark failure
):
    """Run YOLOv5 benchmarks on multiple export formats and log results for model performance evaluation.

    Args:
        weights (Path | str): Path to the model weights file (default: ROOT / "yolov5s.pt").
        imgsz (int): Inference size in pixels (default: 640).
        batch_size (int): Batch size for inference (default: 1).
        data (Path | str): Path to the dataset.yaml file (default: ROOT / "data/coco128.yaml").
        device (str): CUDA device, e.g., '0' or '0,1,2,3' or 'cpu' (default: "").
        half (bool): Use FP16 half-precision inference (default: False).
        test (bool): Test export formats only (default: False).
        pt_only (bool): Test PyTorch format only (default: False).
        hard_fail (bool): Throw an error on benchmark failure if True (default: False).

    Returns:
        None. Logs information about the benchmark results, including the format, size, mAP50-95, and inference time.

    Examples:
        ```python
        $ python benchmarks.py --weights yolov5s.pt --img 640
        ```

        Install required packages:
          $ pip install -r requirements.txt coremltools onnx onnx-simplifier onnxruntime openvino-dev tensorflow-cpu  # CPU support
          $ pip install -r requirements.txt coremltools onnx onnx-simplifier onnxruntime-gpu openvino-dev tensorflow   # GPU support
          $ pip install -U nvidia-tensorrt --index-url https://pypi.ngc.nvidia.com  # TensorRT

        Run benchmarks:
          $ python benchmarks.py --weights yolov5s.pt --img 640

    Notes:
        Supported export formats and models include PyTorch, TorchScript, ONNX, OpenVINO, TensorRT, CoreML,
            TensorFlow SavedModel, TensorFlow GraphDef, TensorFlow Lite, and TensorFlow Edge TPU. Edge TPU and TF.js
            are unsupported.
    """
    y, t = [], time.time()
    device = select_device(device)
    model_type = type(attempt_load(weights, fuse=False))  # DetectionModel, SegmentationModel, etc.
    for i, (name, f, suffix, cpu, gpu) in export.export_formats().iterrows():  # index, (name, file, suffix, CPU, GPU)
        try:
            assert i not in (9, 10), "inference not supported"  # Edge TPU and TF.js are unsupported
            assert i != 5 or platform.system() == "Darwin", "inference only supported on macOS>=10.13"  # CoreML
            if "cpu" in device.type:
                assert cpu, "inference not supported on CPU"
            if "cuda" in device.type:
                assert gpu, "inference not supported on GPU"

            # Export
            if f == "-":
                w = weights  # PyTorch format
            else:
                w = export.run(
                    weights=weights, imgsz=[imgsz], include=[f], batch_size=batch_size, device=device, half=half
                )[-1]  # all others
            assert suffix in str(w), "export failed"

            # Validate
            if model_type == SegmentationModel:
                result = val_seg(data, w, batch_size, imgsz, plots=False, device=device, task="speed", half=half)
                metric = result[0][7]  # (box(p, r, map50, map), mask(p, r, map50, map), *loss(box, obj, cls))
            else:  # DetectionModel:
                result = val_det(data, w, batch_size, imgsz, plots=False, device=device, task="speed", half=half)
                metric = result[0][3]  # (p, r, map50, map, *loss(box, obj, cls))
            speed = result[2][1]  # times (preprocess, inference, postprocess)
            y.append([name, round(file_size(w), 1), round(metric, 4), round(speed, 2)])  # MB, mAP, t_inference
        except Exception as e:
            if hard_fail:
                assert type(e) is AssertionError, f"Benchmark --hard-fail for {name}: {e}"
            LOGGER.warning(f"WARNING ⚠️ Benchmark failure for {name}: {e}")
            y.append([name, None, None, None])  # mAP, t_inference
        if pt_only and i == 0:
            break  # break after PyTorch

    # Print results
    LOGGER.info("\n")
    parse_opt()
    notebook_init()  # print system info
    c = ["Format", "Size (MB)", "mAP50-95", "Inference time (ms)"] if map else ["Format", "Export", "", ""]
    py = pd.DataFrame(y, columns=c)
    LOGGER.info(f"\nBenchmarks complete ({time.time() - t:.2f}s)")
    LOGGER.info(str(py if map else py.iloc[:, :2]))
    if hard_fail and isinstance(hard_fail, str):
        metrics = py["mAP50-95"].array  # values to compare to floor
        floor = eval(hard_fail)  # minimum metric floor to pass, i.e. = 0.29 mAP for YOLOv5n
        assert all(x > floor for x in metrics if pd.notna(x)), f"HARD FAIL: mAP50-95 < floor {floor}"
    return py