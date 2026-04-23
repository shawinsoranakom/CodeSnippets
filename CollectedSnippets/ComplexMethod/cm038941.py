def clear_triton_cache():
    """Clear Triton JIT compilation cache and Python/CUDA memory.

    This helps prevent OOM during tuning with large models (many experts).
    """
    # Force Python garbage collection
    gc.collect()

    # Clear CUDA memory cache
    if torch.cuda.is_available():
        torch.accelerator.empty_cache()

    # Try to clear Triton's runtime cache
    try:
        if (
            hasattr(triton, "runtime")
            and hasattr(triton.runtime, "cache")
            and hasattr(triton.runtime.cache, "clear")
        ):
            triton.runtime.cache.clear()
    except ImportError:
        # Triton not installed, skip cache clearing
        pass
    except AttributeError:
        # Triton version doesn't have expected cache API
        pass
    except Exception as e:
        print(f"Warning: Failed to clear Triton cache: {e}")

    # Additional garbage collection after clearing caches
    gc.collect()