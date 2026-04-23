def clear_all_lru_caches(verbose = True):
    """Clear all LRU caches in loaded modules."""
    cleared_caches = []

    # Modules to skip to avoid warnings
    skip_modules = {
        "torch.distributed",
        "torchaudio",
        "torch._C",
        "torch.distributed.reduce_op",
        "torchaudio.backend",
    }

    # Create a static list of modules to avoid RuntimeError
    modules = list(sys.modules.items())

    # Method 1: Clear caches in all loaded modules
    for module_name, module in modules:
        if module is None:
            continue

        # Skip problematic modules
        if any(module_name.startswith(skip) for skip in skip_modules):
            continue

        try:
            # Look for functions with lru_cache
            for attr_name in dir(module):
                try:
                    # Suppress warnings when checking attributes
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", FutureWarning)
                        warnings.simplefilter("ignore", UserWarning)
                        warnings.simplefilter("ignore", DeprecationWarning)

                    attr = getattr(module, attr_name)
                    if hasattr(attr, "cache_clear"):
                        attr.cache_clear()
                        cleared_caches.append(f"{module_name}.{attr_name}")
                except Exception:
                    continue  # Skip problematic attributes
        except Exception:
            continue  # Skip problematic modules

    # Method 2: Clear specific known caches
    known_caches = [
        "transformers.utils.hub.cached_file",
        "transformers.tokenization_utils_base.get_tokenizer",
        "torch._dynamo.utils.counters",
    ]

    for cache_path in known_caches:
        try:
            parts = cache_path.split(".")
            module = sys.modules.get(parts[0])
            if module:
                obj = module
                for part in parts[1:]:
                    obj = getattr(obj, part, None)
                    if obj is None:
                        break
                if obj and hasattr(obj, "cache_clear"):
                    obj.cache_clear()
                    cleared_caches.append(cache_path)
        except Exception:
            continue  # Skip problematic caches

    if verbose and cleared_caches:
        print(f"Cleared {len(cleared_caches)} LRU caches")