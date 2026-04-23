def flush_memory(flush_compile: bool = True) -> None:
    """Flushes the memory of the current device and, if the flush_compile flag is True, all data related to
    torch.compile."""
    gc.collect()
    # If needed, flush everything related to torch.compile
    if flush_compile:
        # Dynamo resets
        torch._dynamo.reset()
        torch._dynamo.reset_code_caches()
        if hasattr(torch._inductor, "codecache"):
            # Clear FX graph cache
            if hasattr(torch._inductor.codecache, "FxGraphCache"):
                torch._inductor.codecache.FxGraphCache.clear()
            # Clear PyCodeCache
            if hasattr(torch._inductor.codecache, "PyCodeCache"):
                torch._inductor.codecache.PyCodeCache.cache_clear()
            # Clear TritonFuture cache (for async compilation)
            if hasattr(torch._inductor.codecache, "TritonFuture"):
                if hasattr(torch._inductor.codecache.TritonFuture, "_compile_cache"):
                    torch._inductor.codecache.TritonFuture._compile_cache.clear()
    # Clear CUDA cache
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
    elif torch.xpu.is_available():
        torch.xpu.empty_cache()
        torch.xpu.synchronize()
    gc.collect()