def export_coreml(model, im, file, int8, half, nms, mlmodel, prefix=colorstr("CoreML:")):
    """Export a YOLOv5 model to CoreML format with optional NMS, INT8, and FP16 support.

    Args:
        model (torch.nn.Module): The YOLOv5 model to be exported.
        im (torch.Tensor): Example input tensor to trace the model.
        file (pathlib.Path): Path object where the CoreML model will be saved.
        int8 (bool): Flag indicating whether to use INT8 quantization (default is False).
        half (bool): Flag indicating whether to use FP16 quantization (default is False).
        nms (bool): Flag indicating whether to include Non-Maximum Suppression (default is False).
        mlmodel (bool): Flag indicating whether to export as older *.mlmodel format (default is False).
        prefix (str): Prefix string for logging purposes (default is 'CoreML:').

    Returns:
        tuple[pathlib.Path | None, None]: The path to the saved CoreML model file, or (None, None) if there is an error.

    Examples:
        ```python
        from pathlib import Path
        import torch
        from models.yolo import Model
        model = Model(cfg, ch=3, nc=80)
        im = torch.randn(1, 3, 640, 640)
        file = Path("yolov5s_coreml")
        export_coreml(model, im, file, int8=False, half=False, nms=True, mlmodel=False)
        ```

    Notes:
        The exported CoreML model will be saved with a .mlmodel extension.
        Quantization is supported only on macOS.
    """
    check_requirements("coremltools")
    import coremltools as ct

    LOGGER.info(f"\n{prefix} starting export with coremltools {ct.__version__}...")
    if mlmodel:
        f = file.with_suffix(".mlmodel")
        convert_to = "neuralnetwork"
        precision = None
    else:
        f = file.with_suffix(".mlpackage")
        convert_to = "mlprogram"
        precision = ct.precision.FLOAT16 if half else ct.precision.FLOAT32
    if nms:
        model = iOSModel(model, im)
    ts = torch.jit.trace(model, im, strict=False)  # TorchScript model
    ct_model = ct.convert(
        ts,
        inputs=[ct.ImageType("image", shape=im.shape, scale=1 / 255, bias=[0, 0, 0])],
        convert_to=convert_to,
        compute_precision=precision,
    )
    bits, mode = (8, "kmeans") if int8 else (16, "linear") if half else (32, None)
    if bits < 32:
        if mlmodel:
            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore", category=DeprecationWarning
                )  # suppress numpy==1.20 float warning, fixed in coremltools==7.0
                ct_model = ct.models.neural_network.quantization_utils.quantize_weights(ct_model, bits, mode)
        elif bits == 8:
            op_config = ct.optimize.coreml.OpPalettizerConfig(mode=mode, nbits=bits, weight_threshold=512)
            config = ct.optimize.coreml.OptimizationConfig(global_config=op_config)
            ct_model = ct.optimize.coreml.palettize_weights(ct_model, config)
    ct_model.save(f)
    return f, ct_model