def _optimize_det_model(fa: Any, providers) -> None:
    """Replace the detection model's ONNX session with a CoreML-optimized one.

    Folds dynamic Shape→Gather chains into constants (the input size is
    fixed at det_size), eliminating CPU↔ANE partition boundaries in the
    RetinaFace FPN upsampling path.  21ms → 4ms on M3 Max.
    """
    from modules.onnx_optimize import optimize_for_coreml, IS_APPLE_SILICON
    if not IS_APPLE_SILICON:
        return

    det_model = fa.det_model
    model_path = getattr(det_model, 'model_file', None)
    if model_path is None or not os.path.exists(model_path):
        return

    input_shape = (1, 3, DET_SIZE[1], DET_SIZE[0])
    optimized_path = optimize_for_coreml(model_path, input_shape=input_shape)
    if optimized_path == model_path:
        return

    import onnxruntime
    session_options = onnxruntime.SessionOptions()
    session_options.graph_optimization_level = (
        onnxruntime.GraphOptimizationLevel.ORT_ENABLE_ALL
    )

    # Route detection to GPU shader cores (CPUAndGPU) instead of ANE.
    # This lets detection run concurrently with the swap model on the
    # ANE, overlapping the two inference calls.  Detection is fast
    # enough on GPU (~4ms) and this frees ANE for the heavier swap.
    det_providers = []
    for p in providers:
        name = p[0] if isinstance(p, tuple) else p
        if name == "CoreMLExecutionProvider":
            det_providers.append((
                "CoreMLExecutionProvider",
                {"ModelFormat": "MLProgram", "MLComputeUnits": "CPUAndGPU"},
            ))
        else:
            det_providers.append(p)

    det_model.session = onnxruntime.InferenceSession(
        optimized_path, sess_options=session_options, providers=det_providers,
    )