def _short_config(config: str, device: str = "") -> str:
    """Compact label: e.g. 'a100 cudagraphs huggingface training'."""
    c = config
    backend = c
    for s in ("_huggingface_", "_timm_models_", "_torchbench_"):
        if s in c:
            backend = c.split(s)[0]
            break
    backend = backend.removeprefix("inductor_")
    mode = "training" if "training" in c else "inference" if "inference" in c else ""
    suite = ""
    for s in ("huggingface", "timm_models", "torchbench"):
        if s in c:
            suite = s
            break
    parts = [p for p in (device, backend, suite, mode) if p]
    return " ".join(parts)