def _wrap_tma_args(args: list[Any], kernel_fn: CachingAutotuner) -> list[Any]:
    """Wrap tensor args with TMA descriptors where the signature requires them."""
    signature = kernel_fn.triton_meta.get("signature", {})
    sig_items = list(signature.items())

    # Track args index separately from sig_items index since the signature
    # may include constexpr entries that are not present in args.
    tma_indices = []
    arg_idx = 0
    for name, sig_type in sig_items:
        if isinstance(sig_type, str) and sig_type == "constexpr":
            continue
        if isinstance(sig_type, str) and sig_type == "nvTmaDesc":
            raise RuntimeError(
                f"nvTmaDesc (experimental TMA API) is not supported in lazy compile "
                f"for arg '{name}'. Use the stable tensordesc API instead."
            )
        if isinstance(sig_type, str) and sig_type.startswith("tensordesc<"):
            tma_indices.append((arg_idx, name, sig_type))
        arg_idx += 1

    if not tma_indices:
        return args

    from triton.tools.tensor_descriptor import TensorDescriptor

    wrapped = list(args)
    for arg_idx, name, sig_type in tma_indices:
        if arg_idx >= len(wrapped):
            raise RuntimeError(
                f"TMA arg index {arg_idx} for '{name}' exceeds arg count {len(wrapped)}"
            )
        tensor = wrapped[arg_idx]
        # Parse block_shape from tensordesc<dtype[dim0, dim1, ...]>
        match = re.match(r"tensordesc<[^[]*\[([^\]]*)\]", sig_type)
        if match:
            block_shape = [int(x.strip()) for x in match.group(1).split(",")]
            wrapped[arg_idx] = TensorDescriptor.from_tensor(tensor, block_shape)

    return wrapped