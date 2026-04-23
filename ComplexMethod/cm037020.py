def _use_color() -> bool:
    if envs.NO_COLOR or envs.VLLM_LOGGING_COLOR == "0":
        return False
    if envs.VLLM_LOGGING_COLOR == "1":
        return True
    if envs.VLLM_LOGGING_STREAM == "ext://sys.stdout":  # stdout
        return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
    elif envs.VLLM_LOGGING_STREAM == "ext://sys.stderr":  # stderr
        return hasattr(sys.stderr, "isatty") and sys.stderr.isatty()
    return False