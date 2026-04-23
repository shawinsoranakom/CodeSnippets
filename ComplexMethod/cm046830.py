def clear_memory(variables_to_clear = None, verbose = False, clear_all_caches = True):
    """
    Comprehensive memory clearing for persistent memory leaks.

    Args:
        variables_to_clear: List of variable names to clear
        verbose: Print memory status
        clear_all_caches: Clear all types of caches (recommended for memory leaks)
    """

    # Save current logging levels
    saved_log_levels = {}
    for name, logger in logging.Logger.manager.loggerDict.items():
        if isinstance(logger, logging.Logger):
            saved_log_levels[name] = logger.level
    root_level = logging.getLogger().level

    if variables_to_clear is None:
        variables_to_clear = [
            "inputs",
            "model",
            "base_model",
            "processor",
            "tokenizer",
            "base_processor",
            "base_tokenizer",
            "trainer",
            "peft_model",
            "bnb_config",
        ]

    # 1. Clear LRU caches FIRST (very important for memory leaks)
    if clear_all_caches:
        clear_all_lru_caches(verbose)

    # 2. Delete specified variables
    g = globals()
    deleted_vars = []
    for var in variables_to_clear:
        if var in g:
            del g[var]
            deleted_vars.append(var)

    if verbose and deleted_vars:
        print(f"Deleted variables: {deleted_vars}")

    # 3. Multiple garbage collection passes (important for circular references)
    for i in range(3):
        collected = gc.collect()
        if verbose and collected > 0:
            print(f"GC pass {i+1}: collected {collected} objects")

    # 4. CUDA cleanup
    if torch.cuda.is_available():
        # Get memory before cleanup
        if verbose:
            mem_before = torch.cuda.memory_allocated() / 1024**3

        torch.cuda.empty_cache()
        torch.cuda.synchronize()

        # Additional CUDA cleanup for persistent leaks
        if clear_all_caches:
            # Reset memory stats
            torch.cuda.reset_peak_memory_stats()
            torch.cuda.reset_accumulated_memory_stats()

            # Clear JIT cache
            if hasattr(torch.jit, "_state") and hasattr(
                torch.jit._state, "_clear_class_state"
            ):
                torch.jit._state._clear_class_state()

            # Force another CUDA cache clear
            torch.cuda.empty_cache()

        # Final garbage collection
        gc.collect()

        if verbose:
            mem_after = torch.cuda.memory_allocated() / 1024**3
            mem_reserved = torch.cuda.memory_reserved() / 1024**3
            print(
                f"GPU memory - Before: {mem_before:.2f} GB, After: {mem_after:.2f} GB"
            )
            print(f"GPU reserved memory: {mem_reserved:.2f} GB")
            if mem_before > 0:
                print(f"Memory freed: {mem_before - mem_after:.2f} GB")

    # restore original logging levels
    logging.getLogger().setLevel(root_level)
    for name, level in saved_log_levels.items():
        if name in logging.Logger.manager.loggerDict:
            logger = logging.getLogger(name)
            logger.setLevel(level)