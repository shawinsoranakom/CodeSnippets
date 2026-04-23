def get_face_swapper() -> Any:
    global FACE_SWAPPER

    with THREAD_LOCK:
        if FACE_SWAPPER is None:
            # Prefer FP16 on GPUs with Tensor Cores (Turing+) — half the
            # memory bandwidth, faster inference.  Fall back to FP32 for
            # older GPUs (e.g. GTX 16xx) where FP16 can produce NaN.
            fp32_path = os.path.join(models_dir, "inswapper_128.onnx")
            fp16_path = os.path.join(models_dir, "inswapper_128_fp16.onnx")
            use_fp16 = _HAS_TORCH_CUDA and os.path.exists(fp16_path)
            if use_fp16:
                model_path = fp16_path
            elif os.path.exists(fp32_path):
                model_path = fp32_path
            else:
                update_status(f"No inswapper model found in {models_dir}.", NAME)
                return None
            # On Apple Silicon, rewrite Pad(reflect) → Slice+Concat so
            # CoreML can run the entire model in a single partition on
            # the Neural Engine instead of bouncing between CPU and ANE.
            if IS_APPLE_SILICON:
                from modules.onnx_optimize import optimize_for_coreml
                model_path = optimize_for_coreml(model_path)

            update_status(f"Loading face swapper model from: {model_path}", NAME)
            try:
                providers_config = []
                for p in modules.globals.execution_providers:
                    if p == "CoreMLExecutionProvider" and IS_APPLE_SILICON:
                        # Enhanced CoreML configuration for M1-M5
                        providers_config.append((
                            "CoreMLExecutionProvider",
                            {
                                "ModelFormat": "MLProgram",
                                "MLComputeUnits": "ALL",  # Use Neural Engine + GPU + CPU
                                "SpecializationStrategy": "FastPrediction",
                                "AllowLowPrecisionAccumulationOnGPU": 1,
                                "EnableOnSubgraphs": 1,
                            }
                        ))
                    elif p == "CUDAExecutionProvider":
                        # Use bare provider — ONNX Runtime defaults are
                        # fastest on modern GPUs (Blackwell/sm_120).
                        providers_config.append(p)
                    else:
                        providers_config.append(p)
                FACE_SWAPPER = insightface.model_zoo.get_model(
                    model_path,
                    providers=providers_config,
                )
                # Set up CUDA graph session for faster inference
                if _HAS_TORCH_CUDA and any(
                    p == "CUDAExecutionProvider" or
                    (isinstance(p, tuple) and p[0] == "CUDAExecutionProvider")
                    for p in providers_config
                ):
                    _init_cuda_graph_session(model_path, FACE_SWAPPER)
                update_status("Face swapper model loaded successfully.", NAME)
            except Exception as e:
                update_status(f"Error loading face swapper model: {e}", NAME)
                FACE_SWAPPER = None
                return None
    return FACE_SWAPPER