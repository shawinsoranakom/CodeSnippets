def _sanitize_for_embedding(code: str, model_hint: str | None, symbol_hint: str | None) -> str:
    """
    Sanitize code for embedding by replacing model-specific identifiers with generic placeholder.

    Args:
        code (`str`): The source code to sanitize.
        model_hint (`str` or `None`): Hint about the model name (e.g., 'llama').
        symbol_hint (`str` or `None`): Hint about the symbol name (e.g., 'LlamaAttention').

    Returns:
        `str`: The sanitized code with model-specific identifiers replaced by 'Model'.
    """
    base = _strip_source_for_tokens(code)
    variants = set()
    if model_hint:
        variants.add(model_hint)
        variants.add(model_hint.replace("_", ""))
        variants.add(re.sub(r"\d+", "", model_hint))
    if symbol_hint:
        prefix = _leading_symbol_prefix(symbol_hint)
        if prefix:
            variants.add(prefix)
            variants.add(prefix.replace("_", ""))
            variants.add(re.sub(r"\d+", "", prefix))
    variants |= {variant.lower() for variant in list(variants)}
    sanitized = base
    for variant in sorted({x for x in variants if len(x) >= 3}, key=len, reverse=True):
        sanitized = re.sub(re.escape(variant), "Model", sanitized, flags=re.IGNORECASE)
    return sanitized