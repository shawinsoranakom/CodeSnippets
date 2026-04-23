def torch2imx(
    model: torch.nn.Module,
    output_dir: Path | str,
    conf: float,
    iou: float,
    max_det: int,
    metadata: dict | None = None,
    gptq: bool = False,
    dataset=None,
    prefix: str = "",
) -> str:
    """Export YOLO model to IMX format for deployment on Sony IMX500 devices.

    This function quantizes a YOLO model using Model Compression Toolkit (MCT) and exports it to IMX format compatible
    with Sony IMX500 edge devices. It supports both YOLOv8n and YOLO11n models for detection, segmentation, pose
    estimation, and classification tasks.

    Args:
        model (torch.nn.Module): The YOLO model to export. Must be YOLOv8n or YOLO11n.
        output_dir (Path | str): Directory to save the exported IMX model.
        conf (float): Confidence threshold for NMS post-processing.
        iou (float): IoU threshold for NMS post-processing.
        max_det (int): Maximum number of detections to return.
        metadata (dict | None, optional): Metadata to embed in the ONNX model. Defaults to None.
        gptq (bool, optional): Whether to use Gradient-Based Post Training Quantization. If False, uses standard Post
            Training Quantization. Defaults to False.
        dataset (optional): Representative dataset for quantization calibration. Defaults to None.
        prefix (str, optional): Logging prefix string. Defaults to "".

    Returns:
        (str): Path to the exported IMX model directory.

    Raises:
        ValueError: If the model is not a supported YOLOv8n or YOLO11n variant.

    Examples:
        >>> from ultralytics import YOLO
        >>> model = YOLO("yolo11n.pt")
        >>> path = torch2imx(model, "output_dir/", conf=0.25, iou=0.7, max_det=300)

    Notes:
        - Requires model_compression_toolkit, onnx, edgemdt_tpc, and edge-mdt-cl packages
        - Only supports YOLOv8n and YOLO11n models (detection, segmentation, pose, and classification tasks)
        - Output includes quantized ONNX model, IMX binary, and labels.txt file
    """
    import model_compression_toolkit as mct
    import onnx
    from edgemdt_tpc import get_target_platform_capabilities

    LOGGER.info(f"\n{prefix} starting export with model_compression_toolkit {mct.__version__}...")

    def representative_dataset_gen(dataloader=dataset):
        for batch in dataloader:
            img = batch["img"]
            img = img / 255.0
            yield [img]

    # NOTE: need tpc_version to be "4.0" for IMX500 Pose estimation models
    tpc = get_target_platform_capabilities(tpc_version="4.0", device_type="imx500")

    bit_cfg = mct.core.BitWidthConfig()
    mct_config = MCT_CONFIG["YOLO11" if "C2PSA" in model.__str__() else "YOLOv8"][model.task]

    # Check if the model has the expected number of layers
    if len(list(model.modules())) not in mct_config["n_layers"]:
        raise ValueError("IMX export only supported for YOLOv8n and YOLO11n models.")

    for layer_name in mct_config["layer_names"]:
        bit_cfg.set_manual_activation_bit_width([mct.core.common.network_editors.NodeNameFilter(layer_name)], 16)

    config = mct.core.CoreConfig(
        mixed_precision_config=mct.core.MixedPrecisionQuantizationConfig(num_of_images=10),
        quantization_config=mct.core.QuantizationConfig(concat_threshold_update=True),
        bit_width_config=bit_cfg,
    )

    resource_utilization = mct.core.ResourceUtilization(weights_memory=mct_config["weights_memory"])

    quant_model = (
        mct.gptq.pytorch_gradient_post_training_quantization(  # Perform Gradient-Based Post Training Quantization
            model=model,
            representative_data_gen=representative_dataset_gen,
            target_resource_utilization=resource_utilization,
            gptq_config=mct.gptq.get_pytorch_gptq_config(
                n_epochs=1000, use_hessian_based_weights=False, use_hessian_sample_attention=False
            ),
            core_config=config,
            target_platform_capabilities=tpc,
        )[0]
        if gptq
        else mct.ptq.pytorch_post_training_quantization(  # Perform post training quantization
            in_module=model,
            representative_data_gen=representative_dataset_gen,
            target_resource_utilization=resource_utilization,
            core_config=config,
            target_platform_capabilities=tpc,
        )[0]
    )

    if model.task != "classify":
        quant_model = NMSWrapper(
            model=quant_model,
            score_threshold=conf or 0.001,
            iou_threshold=iou,
            max_detections=max_det,
            task=model.task,
        )

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    onnx_model = output_dir / "model_imx.onnx"

    with onnx_export_patch():
        mct.exporter.pytorch_export_model(
            model=quant_model, save_model_path=onnx_model, repr_dataset=representative_dataset_gen
        )

    model_onnx = onnx.load(onnx_model)  # load onnx model
    for k, v in (metadata or {}).items():
        meta = model_onnx.metadata_props.add()
        meta.key, meta.value = k, str(v)

    onnx.save(model_onnx, onnx_model)

    # Find imxconv-pt binary - check venv bin directory first, then PATH
    bin_dir = Path(sys.executable).parent
    imxconv = bin_dir / ("imxconv-pt.exe" if WINDOWS else "imxconv-pt")
    if not imxconv.exists():
        imxconv = which("imxconv-pt")  # fallback to PATH
    if not imxconv:
        raise FileNotFoundError("imxconv-pt not found. Install with: pip install imx500-converter[pt]")

    subprocess.run(
        [str(imxconv), "-i", str(onnx_model), "-o", str(output_dir), "--no-input-persistency", "--overwrite-output"],
        check=True,
    )

    # Needed for imx models.
    with open(output_dir / "labels.txt", "w", encoding="utf-8") as labels_file:
        labels_file.writelines([f"{name}\n" for _, name in model.names.items()])

    return str(output_dir)