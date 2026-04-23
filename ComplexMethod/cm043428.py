def export_engine(
    model, im, file, half, dynamic, simplify, workspace=4, verbose=False, cache="", prefix=colorstr("TensorRT:")
):
    """Export a YOLOv5 model to TensorRT engine format, requiring GPU and TensorRT>=7.0.0.

    Args:
        model (torch.nn.Module): YOLOv5 model to be exported.
        im (torch.Tensor): Input tensor of shape (B, C, H, W).
        file (pathlib.Path): Path to save the exported model.
        half (bool): Set to True to export with FP16 precision.
        dynamic (bool): Set to True to enable dynamic input shapes.
        simplify (bool): Set to True to simplify the model during export.
        workspace (int): Workspace size in GB (default is 4).
        verbose (bool): Set to True for verbose logging output.
        cache (str): Path to save the TensorRT timing cache.
        prefix (str): Log message prefix.

    Returns:
        (pathlib.Path, None): Tuple containing the path to the exported model and None.

    Raises:
        AssertionError: If executed on CPU instead of GPU.
        RuntimeError: If there is a failure in parsing the ONNX file.

    Examples:
        ```python
        from ultralytics import YOLOv5
        import torch
        from pathlib import Path

        model = YOLOv5('yolov5s.pt')  # Load a pre-trained YOLOv5 model
        input_tensor = torch.randn(1, 3, 640, 640).cuda()  # example input tensor on GPU
        export_path = Path('yolov5s.engine')  # export destination

        export_engine(model.model, input_tensor, export_path, half=True, dynamic=True, simplify=True, workspace=8, verbose=True)
        ```
    """
    assert im.device.type != "cpu", "export running on CPU but must be on GPU, i.e. `python export.py --device 0`"
    try:
        import tensorrt as trt
    except Exception:
        if platform.system() == "Linux":
            check_requirements("nvidia-tensorrt", cmds="-U --index-url https://pypi.ngc.nvidia.com")
        import tensorrt as trt

    if trt.__version__[0] == "7":  # TensorRT 7 handling https://github.com/ultralytics/yolov5/issues/6012
        grid = model.model[-1].anchor_grid
        model.model[-1].anchor_grid = [a[..., :1, :1, :] for a in grid]
        export_onnx(model, im, file, 12, dynamic, simplify)  # opset 12
        model.model[-1].anchor_grid = grid
    else:  # TensorRT >= 8
        check_version(trt.__version__, "8.0.0", hard=True)  # require tensorrt>=8.0.0
        export_onnx(model, im, file, 12, dynamic, simplify)  # opset 12
    onnx = file.with_suffix(".onnx")

    LOGGER.info(f"\n{prefix} starting export with TensorRT {trt.__version__}...")
    is_trt10 = int(trt.__version__.split(".")[0]) >= 10  # is TensorRT >= 10
    assert onnx.exists(), f"failed to export ONNX file: {onnx}"
    f = file.with_suffix(".engine")  # TensorRT engine file
    logger = trt.Logger(trt.Logger.INFO)
    if verbose:
        logger.min_severity = trt.Logger.Severity.VERBOSE

    builder = trt.Builder(logger)
    config = builder.create_builder_config()
    if is_trt10:
        config.set_memory_pool_limit(trt.MemoryPoolType.WORKSPACE, workspace << 30)
    else:  # TensorRT versions 7, 8
        config.max_workspace_size = workspace * 1 << 30
    if cache:  # enable timing cache
        Path(cache).parent.mkdir(parents=True, exist_ok=True)
        buf = Path(cache).read_bytes() if Path(cache).exists() else b""
        timing_cache = config.create_timing_cache(buf)
        config.set_timing_cache(timing_cache, ignore_mismatch=True)
    flag = 1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH)
    network = builder.create_network(flag)
    parser = trt.OnnxParser(network, logger)
    if not parser.parse_from_file(str(onnx)):
        raise RuntimeError(f"failed to load ONNX file: {onnx}")

    inputs = [network.get_input(i) for i in range(network.num_inputs)]
    outputs = [network.get_output(i) for i in range(network.num_outputs)]
    for inp in inputs:
        LOGGER.info(f'{prefix} input "{inp.name}" with shape{inp.shape} {inp.dtype}')
    for out in outputs:
        LOGGER.info(f'{prefix} output "{out.name}" with shape{out.shape} {out.dtype}')

    if dynamic:
        if im.shape[0] <= 1:
            LOGGER.warning(f"{prefix} WARNING ⚠️ --dynamic model requires maximum --batch-size argument")
        profile = builder.create_optimization_profile()
        for inp in inputs:
            profile.set_shape(inp.name, (1, *im.shape[1:]), (max(1, im.shape[0] // 2), *im.shape[1:]), im.shape)
        config.add_optimization_profile(profile)

    LOGGER.info(f"{prefix} building FP{16 if builder.platform_has_fast_fp16 and half else 32} engine as {f}")
    if builder.platform_has_fast_fp16 and half:
        config.set_flag(trt.BuilderFlag.FP16)

    build = builder.build_serialized_network if is_trt10 else builder.build_engine
    with build(network, config) as engine, open(f, "wb") as t:
        t.write(engine if is_trt10 else engine.serialize())
    if cache:  # save timing cache
        with open(cache, "wb") as c:
            c.write(config.get_timing_cache().serialize())
    return f, None