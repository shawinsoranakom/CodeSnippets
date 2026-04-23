def wrapper(*args, **kwargs):
        use_cache = kwargs.pop("use_cache", True)

        underline_func = func
        if "functools" in str(func):
            underline_func = func.__wrapped__

        if not use_cache:
            return underline_func(*args, **kwargs)
        if any(not arg.__hash__ for arg in args):
            return underline_func(*args, **kwargs)
        elif any(not kwarg.__hash__ for kwarg in kwargs.values()):
            return underline_func(*args, **kwargs)

        cached = func(*args, **kwargs)
        copied = copy.deepcopy(cached)

        # Preserve _tokenizer for all tokenizers (Rust tokenizer objects don't deep copy properly)
        # This was previously only done for CLIP, but it's needed for all TokenizersBackend tokenizers
        if hasattr(cached, "_tokenizer"):
            # Restore _tokenizer from original since deep copy may have lost or corrupted it
            copied._tokenizer = cached._tokenizer

        if hasattr(copied, "sp_model"):
            copied.sp_model = cached.sp_model

        return copied