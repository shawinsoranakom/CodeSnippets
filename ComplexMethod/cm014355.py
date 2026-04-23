def _inflate_expr(
    arg: T, ref: str, inflate_helper_fn_name: str, skip_size_check: bool = False
) -> tuple[T | torch.Tensor, str, str | None]:
    # Allow custom inflation expressions any object.
    # For example, calling custom image-decoding ops.
    # Or just use "{}" as the format string to ignore size limits.
    if isinstance(arg, InflatableArg):
        if arg.fmt_fn:
            if arg.fmt not in ["{}", ""]:
                raise Exception(  # noqa: TRY002
                    f"Bundled input argument at position '{ref}' has "
                    f"both arg.fmt_fn => \n{arg.fmt_fn} "
                    f"\n and arg.fmt  => {arg.fmt}. "
                    "Please choose `arg.fmt` if the deflater is straightforward or "
                    "`arg.fmt_fn` if you need a function."
                )

            helper_definition = arg.fmt_fn.format(inflate_helper_fn_name)
            expr = f"self.{inflate_helper_fn_name}({ref})"

            return arg.value, expr, helper_definition
        else:
            return arg.value, arg.fmt.format(ref), None

    if isinstance(arg, torch.Tensor):
        # Small-storage tensors can just be saved directly.
        if arg._typed_storage().size() <= MAX_RAW_TENSOR_SIZE or skip_size_check:
            return arg, ref, None
        # Small contiguous tensors can be cloned to have small storage.
        # TODO: Should we do this even for non-contiguous tensors?
        if arg.is_contiguous() and arg.numel() <= MAX_RAW_TENSOR_SIZE:
            return arg.clone(), ref, None
        # Example inputs commonly come from torch.zeros, torch.ones, or torch.full.
        # These can be represented compactly.
        for fmt in [torch.contiguous_format, torch.channels_last]:
            if arg.is_contiguous(memory_format=fmt) and (arg == arg.flatten()[0]).all().item():
                return (arg.flatten()[0].clone().expand(*arg.size()),
                        f"{ref}.contiguous(memory_format={fmt})", None)
        # Prevent big tensors from being bundled by default.
        # TODO: Provide more useful diagnostics.
        raise Exception(  # noqa: TRY002
            f"Bundled input argument at position '{ref}' is "
            f"a tensor with storage size {arg._typed_storage().size()}. "
            f"You probably don't want to bundle this as an input. "
        )
    else:
        return arg, ref, None