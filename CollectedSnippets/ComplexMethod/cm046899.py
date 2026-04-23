def _is_broken_vllm_error(error) -> bool:
    checked = set()
    current = error
    while current is not None and id(current) not in checked:
        checked.add(id(current))
        message = str(current).lower()
        if (
            ("vllm/_c" in message or "vllm._c" in message)
            and (
                "undefined symbol" in message
                or "cannot open shared object file" in message
                or ".so:" in message
            )
        ) or ("vllm" in message and "undefined symbol" in message):
            return True
        # Also catch CUDA shared library mismatches during vllm import
        # e.g. "libcudart.so.12: cannot open shared object file"
        if (
            "libcudart" in message or "libcublas" in message or "libnvrtc" in message
        ) and "cannot open shared object file" in message:
            return True
        current = getattr(current, "__cause__", None) or getattr(
            current, "__context__", None
        )
    return False