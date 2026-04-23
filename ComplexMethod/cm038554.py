def pick_silu_mul_fp8_config(
    args: tuple[Any, ...], config_keys: list[str]
) -> str | None:
    """Pick the best pre-tuned config for the given input shape.

    Selection strategy:
      1. Find the closest intermediate_size among available configs
         (exact match preferred).
      2. Among the num_tokens values tuned for that intermediate_size, pick
         the smallest num_tokens >= the input's num_tokens. If the input is
         larger than all available num_tokens, fall back to the largest.

    Config keys must be "default" or follow the format
    "intermediate_{int}_numtokens_{int}".
    """
    if not config_keys:
        return None

    input_tensor, _scale = args
    intermediate_size = input_tensor.shape[-1] // 2
    num_tokens = input_tensor.view(-1, input_tensor.shape[-1]).shape[0]
    configs: dict[int, list[int]] = {}
    for key in config_keys:
        if key == "default":
            continue
        match = re.fullmatch(r"intermediate_(\d+)_numtokens_(\d+)", key)
        if not match:
            raise ValueError(
                f"Malformed config key '{key}', "
                f"expected format 'intermediate_{{int}}_numtokens_{{int}}'"
            )
        isize_str, ntokens_str = match.groups()
        configs.setdefault(int(isize_str), []).append(int(ntokens_str))

    if not configs:
        return "default" if "default" in config_keys else None

    best_isize = min(configs, key=lambda s: abs(s - intermediate_size))
    available_ntokens = sorted(configs[best_isize])
    best_ntokens = next(
        (n for n in available_ntokens if n >= num_tokens), available_ntokens[-1]
    )

    return f"intermediate_{best_isize}_numtokens_{best_ntokens}"