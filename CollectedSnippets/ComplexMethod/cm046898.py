def _is_broken_causal_conv1d_error(error) -> bool:
    checked = set()
    current = error
    while current is not None and id(current) not in checked:
        checked.add(id(current))
        message = str(current).lower()
        if (
            ("causal_conv1d_cuda" in message and "undefined symbol" in message)
            or ("_zn3c103hip28c10_hip_check_implementation" in message)
            or ("causal_conv1d" in message and "undefined symbol" in message)
        ):
            return True
        current = getattr(current, "__cause__", None) or getattr(
            current, "__context__", None
        )
    return False