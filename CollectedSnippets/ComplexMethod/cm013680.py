def _apply_kernel_options(
    query: Tensor,
    key: Tensor,
    value: Tensor,
    return_lse: bool,
    kernel_options: FlexKernelOptions | None,
    return_aux: AuxRequest | None = None,
) -> _KernelOptionsWithInternals:
    kernel_options = cast(
        _KernelOptionsWithInternals,
        {} if kernel_options is None else dict(kernel_options),
    )

    if "BACKEND" in kernel_options and kernel_options.get(
        "FORCE_USE_FLEX_ATTENTION", False
    ):
        # TODO: remove FORCE_USE_FLEX_ATTENTION once BACKEND is fully adopted.
        raise RuntimeError(
            "BACKEND cannot be combined with legacy FORCE_USE_FLEX_ATTENTION. "
            "BACKEND supersedes the legacy knob; please drop FORCE_USE_FLEX_ATTENTION "
            "and only specify the desired BACKEND."
        )

    if "BACKEND" in kernel_options:
        valid_backends = typing.get_args(_Backend)
        if kernel_options["BACKEND"] not in valid_backends:
            raise ValueError(
                f"Invalid BACKEND value '{kernel_options['BACKEND']}'. "
                f"Must be one of {valid_backends}"
            )

    kernel_options.setdefault("BACKEND", "AUTO")
    kernel_options.setdefault("PRESCALE_QK", False)
    kernel_options.setdefault("ROWS_GUARANTEED_SAFE", False)
    kernel_options.setdefault("BLOCKS_ARE_CONTIGUOUS", False)
    # This forces all biases grad scatters to be done in the DQ iteration loop of the backwards
    kernel_options.setdefault("WRITE_DQ", True)

    any_inputs_on_cpu_device = (
        query.device.type == "cpu"
        or key.device.type == "cpu"
        or value.device.type == "cpu"
    )

    # Determine what auxiliary outputs are needed
    output_lse = return_lse
    output_max = False

    if return_aux is not None:
        # New API takes precedence over legacy parameters
        output_lse = return_aux.lse
        output_max = return_aux.max_scores

    # If forward kernel needs to return logsumexp is decided by this rule internally.
    if "OUTPUT_LOGSUMEXP" in kernel_options:
        raise AssertionError("OUTPUT_LOGSUMEXP must not be in kernel_options")
    kernel_options["OUTPUT_LOGSUMEXP"] = True
    if not output_lse:
        # We used to check if q,k,v required grads but since captured buffers can require grad
        # we always write unless in no_grad
        kernel_options["OUTPUT_LOGSUMEXP"] = torch.is_grad_enabled()
        if any_inputs_on_cpu_device:
            # CPU with torch.compile now supports inference, and will not return lse
            # TODO: support CPU for training and return lse
            kernel_options["OUTPUT_LOGSUMEXP"] = False

    # If forward kernel needs to return max is decided by this rule internally.
    if "OUTPUT_MAX" in kernel_options:
        raise AssertionError("OUTPUT_MAX must not be in kernel_options")
    if kernel_options["BACKEND"] == "FLASH" and output_max:
        raise NotImplementedError(
            "Returning max scores is not supported with BACKEND='FLASH'. "
            "Use return_aux=AuxRequest(lse=True) or omit max_scores."
        )
    kernel_options["OUTPUT_MAX"] = output_max
    if any_inputs_on_cpu_device and output_max:
        # CPU doesn't support returning max yet
        # TODO: support CPU for returning max
        raise NotImplementedError("Returning max scores is not supported on CPU.")
        kernel_options["OUTPUT_MAX"] = False

    return kernel_options