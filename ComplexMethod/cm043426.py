def export_onnx(model, im, file, opset, dynamic, simplify, prefix=colorstr("ONNX:")):
    """Export a YOLOv5 model to ONNX format with dynamic axes support and optional model simplification.

    Args:
        model (torch.nn.Module): The YOLOv5 model to be exported.
        im (torch.Tensor): A sample input tensor for model tracing, usually the shape is (1, 3, height, width).
        file (pathlib.Path | str): The output file path where the ONNX model will be saved.
        opset (int): The ONNX opset version to use for export.
        dynamic (bool): If True, enables dynamic axes for batch, height, and width dimensions.
        simplify (bool): If True, applies ONNX model simplification for optimization.
        prefix (str): A prefix string for logging messages, defaults to 'ONNX:'.

    Returns:
        tuple[pathlib.Path | str, None]: The path to the saved ONNX model file and None (consistent with decorator).

    Raises:
        ImportError: If required libraries for export (e.g., 'onnx', 'onnx-simplifier') are not installed.
        AssertionError: If the simplification check fails.

    Examples:
        ```python
        from pathlib import Path
        import torch
        from models.experimental import attempt_load
        from utils.torch_utils import select_device

        # Load model
        weights = 'yolov5s.pt'
        device = select_device('')
        model = attempt_load(weights, map_location=device)

        # Example input tensor
        im = torch.zeros(1, 3, 640, 640).to(device)

        # Export model
        file_path = Path('yolov5s.onnx')
        export_onnx(model, im, file_path, opset=12, dynamic=True, simplify=True)
        ```

    Notes:
        The required packages for this function can be installed via:
        ```
        pip install onnx onnx-simplifier onnxruntime onnxruntime-gpu
        ```
    """
    check_requirements(("onnx>=1.12.0", "onnxscript"))
    import onnx

    LOGGER.info(f"\n{prefix} starting export with onnx {onnx.__version__}...")
    f = str(file.with_suffix(".onnx"))

    output_names = ["output0", "output1"] if isinstance(model, SegmentationModel) else ["output0"]
    if dynamic:
        dynamic = {"images": {0: "batch", 2: "height", 3: "width"}}  # shape(1,3,640,640)
        if isinstance(model, SegmentationModel):
            dynamic["output0"] = {0: "batch", 1: "anchors"}  # shape(1,25200,85)
            dynamic["output1"] = {0: "batch", 2: "mask_height", 3: "mask_width"}  # shape(1,32,160,160)
        elif isinstance(model, DetectionModel):
            dynamic["output0"] = {0: "batch", 1: "anchors"}  # shape(1,25200,85)

    torch.onnx.export(
        model.cpu() if dynamic else model,  # --dynamic only compatible with cpu
        im.cpu() if dynamic else im,
        f,
        verbose=False,
        opset_version=opset,
        do_constant_folding=True,  # WARNING: DNN inference with torch>=1.12 may require do_constant_folding=False
        input_names=["images"],
        output_names=output_names,
        dynamic_axes=dynamic or None,
    )

    # Checks
    model_onnx = onnx.load(f)  # load onnx model
    onnx.checker.check_model(model_onnx)  # check onnx model

    # Metadata
    d = {"stride": int(max(model.stride)), "names": model.names}
    for k, v in d.items():
        meta = model_onnx.metadata_props.add()
        meta.key, meta.value = k, str(v)
    onnx.save(model_onnx, f)

    # Simplify
    if simplify:
        try:
            cuda = torch.cuda.is_available()
            check_requirements(("onnxruntime-gpu" if cuda else "onnxruntime", "onnxslim"))
            import onnxslim

            LOGGER.info(f"{prefix} slimming with onnxslim {onnxslim.__version__}...")
            model_onnx = onnxslim.slim(model_onnx)
            onnx.save(model_onnx, f)
        except Exception as e:
            LOGGER.info(f"{prefix} simplifier failure: {e}")
    return f, model_onnx