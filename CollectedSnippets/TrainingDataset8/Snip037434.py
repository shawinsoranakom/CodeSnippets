def _get_signature(f):
    is_delta_gen = False
    with contextlib.suppress(AttributeError):
        is_delta_gen = f.__module__ == "streamlit.delta_generator"
        # Functions such as numpy.minimum don't have a __module__ attribute,
        # since we're only using it to check if its a DeltaGenerator, its ok
        # to continue

    sig = ""

    with contextlib.suppress(ValueError):
        sig = str(inspect.signature(f))
    if is_delta_gen:
        for prefix in CONFUSING_STREAMLIT_SIG_PREFIXES:
            if sig.startswith(prefix):
                sig = sig.replace(prefix, "(")
                break

    return sig