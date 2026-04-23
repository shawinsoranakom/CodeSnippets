def optimize_for_coreml(model_path: str, input_shape: tuple = None) -> str:
    """Return path to a CoreML-optimized ONNX model.

    Applies all applicable optimizations and caches the result next to
    the original model (with ``_coreml`` suffix).

    Args:
        model_path: Path to the original ONNX model.
        input_shape: Optional fixed input shape (e.g. ``(1, 3, 640, 640)``).
            When provided, enables Shape/Gather constant folding.

    Returns the optimized path, or the original path if no optimizations
    apply or we're not on Apple Silicon.
    """
    if not IS_APPLE_SILICON:
        return model_path

    base, ext = os.path.splitext(model_path)
    optimized_path = f"{base}_coreml{ext}"
    if os.path.exists(optimized_path):
        if os.path.getmtime(optimized_path) >= os.path.getmtime(model_path):
            return optimized_path

    import onnx
    from onnx import numpy_helper

    model = onnx.load(model_path)
    changed = False

    if _fold_shape_gather(model, input_shape):
        changed = True

    # TODO(ort>=1.26): drop this pass. Fixed upstream by microsoft/onnxruntime#28073.
    if _decompose_reflect_pad(model):
        changed = True

    if _decompose_split(model):
        changed = True

    # TODO: drop this pass once microsoft/onnxruntime#28180 ships. The CoreML
    # Gather op builder rejects rank-0 (scalar) indices; we widen them to [1]
    # + Squeeze so StyleGAN-family models (GFPGAN) stay on ANE.
    if _rewrite_scalar_gather(model):
        changed = True

    if not changed:
        return model_path

    # Preserve insightface's emap convention: the INSwapper class reads
    # graph.initializer[-1] as the embedding map.  If the original model
    # had a (512, 512) matrix as its last initializer, keep it last.
    _preserve_emap_position(model, numpy_helper)

    onnx.save(model, optimized_path)
    return optimized_path