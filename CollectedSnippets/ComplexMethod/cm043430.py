def run(
    data=ROOT / "data/coco128.yaml",  # 'dataset.yaml path'
    weights=ROOT / "yolov5s.pt",  # weights path
    imgsz=(640, 640),  # image (height, width)
    batch_size=1,  # batch size
    device="cpu",  # cuda device, i.e. 0 or 0,1,2,3 or cpu
    include=("torchscript", "onnx"),  # include formats
    half=False,  # FP16 half-precision export
    inplace=False,  # set YOLOv5 Detect() inplace=True
    keras=False,  # use Keras
    optimize=False,  # TorchScript: optimize for mobile
    int8=False,  # CoreML/TF INT8 quantization
    per_tensor=False,  # TF per tensor quantization
    dynamic=False,  # ONNX/TF/TensorRT: dynamic axes
    cache="",  # TensorRT: timing cache path
    simplify=False,  # ONNX: simplify model
    mlmodel=False,  # CoreML: Export in *.mlmodel format
    opset=12,  # ONNX: opset version
    verbose=False,  # TensorRT: verbose log
    workspace=4,  # TensorRT: workspace size (GB)
    nms=False,  # TF: add NMS to model
    agnostic_nms=False,  # TF: add agnostic NMS to model
    topk_per_class=100,  # TF.js NMS: topk per class to keep
    topk_all=100,  # TF.js NMS: topk for all classes to keep
    iou_thres=0.45,  # TF.js NMS: IoU threshold
    conf_thres=0.25,  # TF.js NMS: confidence threshold
):
    """Exports a YOLOv5 model to specified formats including ONNX, TensorRT, CoreML, and TensorFlow.

    Args:
        data (str | Path): Path to the dataset YAML configuration file. Default is 'data/coco128.yaml'.
        weights (str | Path): Path to the pretrained model weights file. Default is 'yolov5s.pt'.
        imgsz (tuple): Image size as (height, width). Default is (640, 640).
        batch_size (int): Batch size for exporting the model. Default is 1.
        device (str): Device to run the export on, e.g., '0' for GPU, 'cpu' for CPU. Default is 'cpu'.
        include (tuple): Formats to include in the export. Default is ('torchscript', 'onnx').
        half (bool): Flag to export model with FP16 half-precision. Default is False.
        inplace (bool): Set the YOLOv5 Detect() module inplace=True. Default is False.
        keras (bool): Flag to use Keras for TensorFlow SavedModel export. Default is False.
        optimize (bool): Optimize TorchScript model for mobile deployment. Default is False.
        int8 (bool): Apply INT8 quantization for CoreML or TensorFlow models. Default is False.
        per_tensor (bool): Apply per tensor quantization for TensorFlow models. Default is False.
        dynamic (bool): Enable dynamic axes for ONNX, TensorFlow, or TensorRT exports. Default is False.
        cache (str): TensorRT timing cache path. Default is an empty string.
        simplify (bool): Simplify the ONNX model during export. Default is False.
        opset (int): ONNX opset version. Default is 12.
        verbose (bool): Enable verbose logging for TensorRT export. Default is False.
        workspace (int): TensorRT workspace size in GB. Default is 4.
        nms (bool): Add non-maximum suppression (NMS) to the TensorFlow model. Default is False.
        agnostic_nms (bool): Add class-agnostic NMS to the TensorFlow model. Default is False.
        topk_per_class (int): Top-K boxes per class to keep for TensorFlow.js NMS. Default is 100.
        topk_all (int): Top-K boxes for all classes to keep for TensorFlow.js NMS. Default is 100.
        iou_thres (float): IoU threshold for NMS. Default is 0.45.
        conf_thres (float): Confidence threshold for NMS. Default is 0.25.
        mlmodel (bool): Flag to use *.mlmodel for CoreML export. Default is False.

    Returns:
        None

    Examples:
        ```python
        run(
            data="data/coco128.yaml",
            weights="yolov5s.pt",
            imgsz=(640, 640),
            batch_size=1,
            device="cpu",
            include=("torchscript", "onnx"),
            half=False,
            inplace=False,
            keras=False,
            optimize=False,
            int8=False,
            per_tensor=False,
            dynamic=False,
            cache="",
            simplify=False,
            opset=12,
            verbose=False,
            mlmodel=False,
            workspace=4,
            nms=False,
            agnostic_nms=False,
            topk_per_class=100,
            topk_all=100,
            iou_thres=0.45,
            conf_thres=0.25,
        )
        ```

    Notes:
        - Model export is based on the specified formats in the 'include' argument.
        - Be cautious of combinations where certain flags are mutually exclusive, such as `--half` and `--dynamic`.
    """
    t = time.time()
    include = [x.lower() for x in include]  # to lowercase
    fmts = tuple(export_formats()["Argument"][1:])  # --include arguments
    flags = [x in include for x in fmts]
    assert sum(flags) == len(include), f"ERROR: Invalid --include {include}, valid --include arguments are {fmts}"
    jit, onnx, xml, engine, coreml, saved_model, pb, tflite, edgetpu, tfjs, paddle = flags  # export booleans
    file = Path(url2file(weights) if str(weights).startswith(("http:/", "https:/")) else weights)  # PyTorch weights

    # Load PyTorch model
    device = select_device(device)
    if half:
        assert device.type != "cpu" or coreml, "--half only compatible with GPU export, i.e. use --device 0"
        assert not dynamic, "--half not compatible with --dynamic, i.e. use either --half or --dynamic but not both"
    model = attempt_load(weights, device=device, inplace=True, fuse=True)  # load FP32 model

    # Checks
    imgsz *= 2 if len(imgsz) == 1 else 1  # expand
    if optimize:
        assert device.type == "cpu", "--optimize not compatible with cuda devices, i.e. use --device cpu"

    # Input
    gs = int(max(model.stride))  # grid size (max stride)
    imgsz = [check_img_size(x, gs) for x in imgsz]  # verify img_size are gs-multiples
    ch = next(model.parameters()).size(1)  # require input image channels
    im = torch.zeros(batch_size, ch, *imgsz).to(device)  # image size(1,3,320,192) BCHW iDetection

    # Update model
    model.eval()
    for k, m in model.named_modules():
        if isinstance(m, Detect):
            m.inplace = inplace
            m.dynamic = dynamic
            m.export = True

    for _ in range(2):
        y = model(im)  # dry runs
    if half and not coreml:
        im, model = im.half(), model.half()  # to FP16
    shape = tuple((y[0] if isinstance(y, tuple) else y).shape)  # model output shape
    metadata = {"stride": int(max(model.stride)), "names": model.names}  # model metadata
    LOGGER.info(f"\n{colorstr('PyTorch:')} starting from {file} with output shape {shape} ({file_size(file):.1f} MB)")

    # Exports
    f = [""] * len(fmts)  # exported filenames
    warnings.filterwarnings(action="ignore", category=torch.jit.TracerWarning)  # suppress TracerWarning
    if jit:  # TorchScript
        f[0], _ = export_torchscript(model, im, file, optimize)
    if engine:  # TensorRT required before ONNX
        f[1], _ = export_engine(model, im, file, half, dynamic, simplify, workspace, verbose, cache)
    if onnx or xml:  # OpenVINO requires ONNX
        f[2], _ = export_onnx(model, im, file, opset, dynamic, simplify)
    if xml:  # OpenVINO
        f[3], _ = export_openvino(file, metadata, half, int8, data)
    if coreml:  # CoreML
        f[4], ct_model = export_coreml(model, im, file, int8, half, nms, mlmodel)
        if nms:
            pipeline_coreml(ct_model, im, file, model.names, y, mlmodel)
    if any((saved_model, pb, tflite, edgetpu, tfjs)):  # TensorFlow formats
        assert not tflite or not tfjs, "TFLite and TF.js models must be exported separately, please pass only one type."
        assert not isinstance(model, ClassificationModel), "ClassificationModel export to TF formats not yet supported."
        f[5], s_model = export_saved_model(
            model.cpu(),
            im,
            file,
            dynamic,
            tf_nms=nms or agnostic_nms or tfjs,
            agnostic_nms=agnostic_nms or tfjs,
            topk_per_class=topk_per_class,
            topk_all=topk_all,
            iou_thres=iou_thres,
            conf_thres=conf_thres,
            keras=keras,
        )
        if pb or tfjs:  # pb prerequisite to tfjs
            f[6], _ = export_pb(s_model, file)
        if tflite or edgetpu:
            f[7], _ = export_tflite(
                s_model, im, file, int8 or edgetpu, per_tensor, data=data, nms=nms, agnostic_nms=agnostic_nms
            )
            if edgetpu:
                f[8], _ = export_edgetpu(file)
            add_tflite_metadata(f[8] or f[7], metadata, num_outputs=len(s_model.outputs))
        if tfjs:
            f[9], _ = export_tfjs(file, int8)
    if paddle:  # PaddlePaddle
        f[10], _ = export_paddle(model, im, file, metadata)

    # Finish
    f = [str(x) for x in f if x]  # filter out '' and None
    if any(f):
        cls, det, seg = (isinstance(model, x) for x in (ClassificationModel, DetectionModel, SegmentationModel))  # type
        det &= not seg  # segmentation models inherit from SegmentationModel(DetectionModel)
        dir = Path("segment" if seg else "classify" if cls else "")
        h = "--half" if half else ""  # --half FP16 inference arg
        s = (
            "# WARNING ⚠️ ClassificationModel not yet supported for PyTorch Hub AutoShape inference"
            if cls
            else "# WARNING ⚠️ SegmentationModel not yet supported for PyTorch Hub AutoShape inference"
            if seg
            else ""
        )
        LOGGER.info(
            f"\nExport complete ({time.time() - t:.1f}s)"
            f"\nResults saved to {colorstr('bold', file.parent.resolve())}"
            f"\nDetect:          python {dir / ('detect.py' if det else 'predict.py')} --weights {f[-1]} {h}"
            f"\nValidate:        python {dir / 'val.py'} --weights {f[-1]} {h}"
            f"\nPyTorch Hub:     model = torch.hub.load('ultralytics/yolov5', 'custom', '{f[-1]}')  {s}"
            f"\nVisualize:       https://netron.app"
        )
    return f