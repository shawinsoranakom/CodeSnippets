def torch2coreml(
    model: nn.Module,
    inputs: list,
    im: torch.Tensor,
    classifier_names: list[str] | None,
    output_file: Path | str | None = None,
    mlmodel: bool = False,
    half: bool = False,
    int8: bool = False,
    metadata: dict | None = None,
    prefix: str = "",
) -> Any:
    """Export a PyTorch model to CoreML ``.mlpackage`` or ``.mlmodel`` format.

    Args:
        model (nn.Module): The PyTorch model to export.
        inputs (list): CoreML input descriptions for the model.
        im (torch.Tensor): Example input tensor for tracing.
        classifier_names (list[str] | None): Class names for classifier config, or None if not a classifier.
        output_file (Path | str | None): Output file path, or None to skip saving.
        mlmodel (bool): Whether to export as ``.mlmodel`` (neural network) instead of ``.mlpackage`` (ML program).
        half (bool): Whether to quantize to FP16.
        int8 (bool): Whether to quantize to INT8.
        metadata (dict | None): Metadata to embed in the CoreML model.
        prefix (str): Prefix for log messages.

    Returns:
        (ct.models.MLModel): The converted CoreML model.
    """
    import coremltools as ct

    LOGGER.info(f"\n{prefix} starting export with coremltools {ct.__version__}...")
    ts = torch.jit.trace(model.eval(), im, strict=False)  # TorchScript model

    # Based on apple's documentation it is better to leave out the minimum_deployment target and let that get set
    # Internally based on the model conversion and output type.
    # Setting minimum_deployment_target >= iOS16 will require setting compute_precision=ct.precision.FLOAT32.
    # iOS16 adds in better support for FP16, but none of the CoreML NMS specifications handle FP16 as input.
    ct_model = ct.convert(
        ts,
        inputs=inputs,
        classifier_config=ct.ClassifierConfig(classifier_names) if classifier_names else None,
        convert_to="neuralnetwork" if mlmodel else "mlprogram",
    )
    bits, mode = (8, "kmeans") if int8 else (16, "linear") if half else (32, None)
    if bits < 32:
        if "kmeans" in mode:
            from ultralytics.utils.checks import check_requirements

            check_requirements("scikit-learn")  # scikit-learn package required for k-means quantization
        if mlmodel:
            ct_model = ct.models.neural_network.quantization_utils.quantize_weights(ct_model, bits, mode)
        elif bits == 8:  # mlprogram already quantized to FP16
            import coremltools.optimize.coreml as cto

            op_config = cto.OpPalettizerConfig(mode="kmeans", nbits=bits, weight_threshold=512)
            config = cto.OptimizationConfig(global_config=op_config)
            ct_model = cto.palettize_weights(ct_model, config=config)

    m = dict(metadata or {})  # copy to avoid mutating original
    ct_model.short_description = m.pop("description", "")
    ct_model.author = m.pop("author", "")
    ct_model.license = m.pop("license", "")
    ct_model.version = m.pop("version", "")
    ct_model.user_defined_metadata.update({k: str(v) for k, v in m.items()})

    if output_file is not None:
        try:
            ct_model.save(str(output_file))  # save *.mlpackage
        except Exception as e:
            LOGGER.warning(
                f"{prefix} CoreML export to *.mlpackage failed ({e}), reverting to *.mlmodel export. "
                f"Known coremltools Python 3.11 and Windows bugs https://github.com/apple/coremltools/issues/1928."
            )
            output_file = Path(output_file).with_suffix(".mlmodel")
            ct_model.save(str(output_file))
    return ct_model