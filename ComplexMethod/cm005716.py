def _get_base_kwargs_class(cls):
    """
    Get the root/base TypedDict class by walking the inheritance chain.
    For model-specific kwargs like ComplexProcessingKwargs(ProcessingKwargs), returns ProcessingKwargs.
    For model-specific kwargs like DummyImageProcessorKwargs(ImagesKwargs), returns ImagesKwargs.

    Compatibility: On Python < 3.12, non-generic TypedDict subclasses do not have __orig_bases__ set
    (cpython#103699). We fall back to naming heuristics (e.g. *ImageProcessorKwargs -> ImagesKwargs).
    """
    current = cls
    while True:
        bases = typing_extensions.get_original_bases(current)
        parent = None
        for base in bases:
            if isinstance(base, type) and base not in (dict, object):
                if getattr(base, "__name__", "") == "TypedDict" and getattr(base, "__module__", "") == "typing":
                    continue
                parent = base
                break
        if parent is None:
            # Python < 3.12 fallback: use naming heuristics
            base_name = _get_base_kwargs_class_from_name(current.__name__)
            if base_name is not None:
                global _BASIC_KWARGS_CLASSES
                if _BASIC_KWARGS_CLASSES is None:
                    from transformers.processing_utils import (
                        AudioKwargs,
                        ImagesKwargs,
                        ProcessingKwargs,
                        TextKwargs,
                        VideosKwargs,
                    )

                    _BASIC_KWARGS_CLASSES = {
                        "ImagesKwargs": ImagesKwargs,
                        "ProcessingKwargs": ProcessingKwargs,
                        "TextKwargs": TextKwargs,
                        "VideosKwargs": VideosKwargs,
                        "AudioKwargs": AudioKwargs,
                    }
                parent = _BASIC_KWARGS_CLASSES[base_name]
        if parent is None or parent == current:
            return current
        current = parent