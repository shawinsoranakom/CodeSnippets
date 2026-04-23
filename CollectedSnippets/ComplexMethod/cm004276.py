def _load_class_with_fallback(mapping, backend):
    """
    Load an image processor class from a backend-to-class mapping, with fallback.

    Tries the requested backend first, then the opposite standard backend,
    then any remaining backends. Works with both string class names and resolved class objects.

    Unavailable backends are detected via DummyObject: classes whose required libraries are missing
    are represented as DummyObject subclasses (is_dummy=True). When the torchvision backend is
    missing but a PIL variant exists, _LazyModule transparently returns the PIL class with its own
    warning, so _load_class_with_fallback naturally receives a usable class without extra gating.

    Args:
        mapping: dict mapping backend names (str) to class names (str) or class objects (type).
        backend: the preferred backend name (e.g. "torchvision", "pil").

    Returns:
        The loaded class, or None if no class could be loaded.
    """
    backends_to_try = [backend] + [k for k in mapping if k != backend]

    for b in backends_to_try:
        value = mapping.get(b)
        if value is None:
            continue

        # Value can be a class object (from resolved mapping) or a string class name
        if isinstance(value, type):
            processor_class = value
        else:
            processor_class = get_image_processor_class_from_name(value)

        if processor_class is None or getattr(processor_class, "is_dummy", False):
            continue

        if b != backend:
            logger.warning_once(f"Requested {backend} backend is not available. Falling back to {b} backend.")
        return processor_class

    return None