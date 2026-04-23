def _checkpoint_without_reentrant_generator(
    fn,
    preserve_rng_state=True,
    context_fn: Callable[[], Tuple[ContextManager, ContextManager]] = noop_context_fn,
    determinism_check: str = _DEFAULT_DETERMINISM_MODE,
    debug: bool = False,
    early_stop: bool = True,
    *args,
    **kwargs
):
    """Checkpointing without reentrant autograd.

    Args:
        fn: describes what to run in the forward pass of the model or
            part of the model. It should also know how to handle the inputs
            passed as the tuple. For example, in LSTM, if user passes
            ``(activation, hidden)``, :attr:`function` should correctly use the
            first input as ``activation`` and the second input as ``hidden``
        preserve_rng_state(bool, optional):  Omit stashing and restoring
            the RNG state during each checkpoint.
            Default: ``True``
        context_fn(Callable, optional): A callable returning a tuple of two
            context managers. The function and its recomputation will be run
            under the first and second context managers respectively.
        determinism_check(str, optional): A string specifying the determinism
            check to perform. By default it is set to ``"default"`` which
            compares the shapes, dtypes, and devices of the recomputed tensors
            against those the saved tensors. To turn off this check, specify
            ``"none"``. Currently these are the only two supported values.
            Please open an issue if you would like to see more determinism
            checks.
        debug(bool, optional): If ``True``, error messages will also include
            a trace of the operators ran during the original forward computation
            as well as the recomputation.
        early_stop(bool, optional): If ``True``, non-reentrant checkpoint stops
            recomputation as soon as it has computed all needed Tensors. Can be
            overridden globally using :func:`set_checkpoint_early_stop` context
            manager. Default: ``True``.
        *args: Arguments to pass in to the given ``function``.
        **kwargs: Keyword arguments to pass into the given ``function``.
    """
    unpack_error_cb = None

    if _checkpoint_debug_enabled if _checkpoint_debug_enabled is not None else debug:
        if context_fn is not noop_context_fn:
            raise ValueError(
                "debug=True is incompatible with non-default context_fn"
            )
        context_fn, unpack_error_cb = _get_debug_context_and_cb()

    if determinism_check in _allowed_determinism_checks_to_fns:
        metadata_fn = _allowed_determinism_checks_to_fns[determinism_check]
    else:
        raise ValueError(
            f"determinism_check should be one of {list(_allowed_determinism_checks_to_fns.keys())}, "
            f"but got {determinism_check}"
        )

    device_type = _infer_device_type(*args)
    device_module = _get_device_module(device_type)
    forward_context, recompute_context = context_fn()
    if _is_compiling(fn, args, kwargs) and context_fn is not noop_context_fn:
        if (
            not isinstance(forward_context, TorchDispatchMode)
            or not isinstance(recompute_context, TorchDispatchMode)
        ):
            raise AssertionError(
                "In torch.compile mode, `context_fn` arg passed to `torch.utils.checkpoint` "
                "must generate a tuple of two `TorchDispatchMode`s."
            )
    # Accommodates the (remote) possibility that autocast is enabled for cpu AND gpu.
    device_autocast_kwargs, cpu_autocast_kwargs = _get_autocast_kwargs(device_type=device_type)

    if preserve_rng_state:
        fwd_cpu_state = torch.get_rng_state()
        # Don't eagerly initialize the cuda context by accident.
        # (If the user intends that the context is initialized later, within their
        # run_function, we SHOULD actually stash the cuda state here.  Unfortunately,
        # we have no way to anticipate this will happen before we run the function.
        # If they do so, we raise an error.)
        had_device_in_fwd = False
        if getattr(device_module, "_initialized", False):
            had_device_in_fwd = True
            fwd_devices, fwd_device_states = get_device_states(*args)

    from torch.overrides import _get_current_function_mode_stack
    from torch.utils._device import DeviceContext

    # recompute_fn should respect the device context of the original forward
    device_ctx = next(
        filter(
            lambda mode: isinstance(mode, DeviceContext),
            reversed(_get_current_function_mode_stack()),
        ),
        contextlib.nullcontext(),
    )
    error_on_nested_fx_trace = torch._dynamo.config.error_on_nested_fx_trace
    is_non_strict_tracing = torch.compiler._is_non_strict_tracing()

    def recompute_fn(*args) -> None:
        # This will be called later during recomputation. This wrapping enables
        # the necessary global state to be captured.
        rng_devices = []
        if preserve_rng_state and had_device_in_fwd:
            rng_devices = fwd_devices
        with torch.random.fork_rng(
            devices=rng_devices, enabled=preserve_rng_state, device_type=device_type
        ):
            if preserve_rng_state:
                torch.set_rng_state(fwd_cpu_state)
                if had_device_in_fwd:
                    set_device_states(fwd_devices, fwd_device_states, device_type=device_type)

            device_autocast_ctx = torch.amp.autocast(
                device_type=device_type, **device_autocast_kwargs
            ) if torch.amp.is_autocast_available(device_type) else contextlib.nullcontext()
            nested_fx_trace_ctx = (
                torch._dynamo.config.patch(
                    error_on_nested_fx_trace=error_on_nested_fx_trace
                )
                if is_non_strict_tracing
                else contextlib.nullcontext()
            )
            with (
                device_autocast_ctx,
                torch.amp.autocast("cpu", **cpu_autocast_kwargs),
                recompute_context,
                device_ctx,
                nested_fx_trace_ctx,
            ):  # type: ignore[attr-defined]
                fn(*args, **kwargs)

    new_frame = _CheckpointFrame(
        recompute_fn,
        _enable_checkpoint_early_stop if _enable_checkpoint_early_stop is not None else early_stop,
        unpack_error_cb,
        metadata_fn
    )

    if not torch.is_grad_enabled():
        yield
        return

    new_frame.save_inputs(*args)

    with _checkpoint_hook(new_frame), forward_context:
        yield
    new_frame.forward_completed = True

    if getattr(device_module, "_initialized", False) and \
       preserve_rng_state and not had_device_in_fwd:  # type: ignore[possibly-undefined]
        # Device was not initialized before running the forward, so we didn't
        # stash the device state.
        raise RuntimeError(
            "PyTorch's device state was initialized in the forward pass "
            "of a Checkpoint, which is not allowed. Please open an issue "
            "if you need this feature."
        )

    return