def proxy_call(
    proxy_mode: ProxyTorchDispatchMode,
    func: OpOverload,
    pre_dispatch: bool,
    args: tuple[object, ...],
    kwargs: dict[str, object],
) -> object:
    unrecognized_types: list[type] = []
    flat_args_kwargs, spec = pytree.tree_flatten((args, kwargs))

    def can_handle_tensor(x: Tensor) -> bool:
        r = type(x) in HANDLED_TYPES or has_proxy_slot(x, proxy_mode.tracer)
        if proxy_mode._allow_fake_constant:
            r = r or type(x) is torch._subclasses.FakeTensor
        if not r:
            unrecognized_types.append(type(x))
        return r

    # If there are any tensor subclasses, we need to handle those tensor subclasses first
    # TODO: we could use types to test this
    if not all(can_handle_tensor(x) for x in flat_args_kwargs if isinstance(x, Tensor)):
        not_implemented_log.debug(
            "ProxyTensorMode tensors without proxy had unrecognized subclasses: %s",
            unrecognized_types,
        )
        return NotImplemented

    r = maybe_handle_decomp(proxy_mode, func, args, kwargs)
    if r is not NotImplemented:
        _maybe_record_pointwise_barrier(func, proxy_mode)
        return r

    # For pre-autograd tracing, we do not want to run CompositeImplicit decomps.
    if (
        not pre_dispatch
        and func
        not in [
            torch.ops.aten.size.default,
            torch.ops.aten.stride.default,
            torch.ops.aten.storage_offset.default,
        ]
        and autograd_would_have_decomposed(func, flat_args_kwargs)
    ):
        with proxy_mode:
            r = func.decompose(*args, **kwargs)
            if r is not NotImplemented:
                return r

    if func is torch.ops.aten.is_nonzero.default:
        with proxy_mode:
            torch._check(
                args[0].numel() == 1,  # type: ignore[attr-defined]
                lambda: "Boolean value of Tensor with more than one value is ambiguous",
            )
            return (args[0] != 0).item()  # type: ignore[attr-defined]

    tracer = proxy_mode.tracer
    f_flat_args_kwargs, proxy_flat_args_kwargs, all_constant = (
        _fetch_proxies_and_all_constant_flag(flat_args_kwargs, tracer)
    )

    if torch.Tag.data_dependent_output in func.tags:
        # Check if all of the Tensor inputs are constants
        if all_constant:
            const_flat_args_kwargs = [
                t.constant if isinstance(t, _ProxyTensor) else t
                for t in f_flat_args_kwargs
            ]
            const_args, const_kwargs = pytree.tree_unflatten(
                const_flat_args_kwargs, spec
            )
            with unset_fake_temporarily():
                return func(*const_args, **const_kwargs)
        # If any of the Tensor inputs are "real" (not FakeTensor), we may
        # incorrectly burn in constants by allowing this access.  Raise
        # an error in this case
        if proxy_mode._error_on_data_dependent_ops and pytree.tree_all_only(
            Tensor, lambda t: not is_fake(t), (args, kwargs)
        ):
            raise RuntimeError(
                f"It appears that you're trying to get value out of a tracing tensor with {func} - erroring out! "
                "It's likely that this is caused by data-dependent control flow or similar.  "
                "It may be possible to trace this with dynamic shapes; try setting tracing_mode='symbolic' "
                "in your make_fx call."
            )

    proxy_args, proxy_kwargs = pytree.tree_unflatten(proxy_flat_args_kwargs, spec)

    # When we trace through a torch.tensor invocation, you never actually
    # see a torch.ops.aten.tensor call. Instead, the way this function is
    # implemented internally is that we allocate a plain tensor (this is
    # *guaranteed* to be a plain tensor, we disable all modes when doing
    # so), and then call at::lift_fresh on it (to give modes a chance to do
    # their stuff).  Furthermore, the tensor argument to lift_fresh is guaranteed
    # to be freshly allocated, so we want lift_fresh to be a no-op (directly
    # returning the input argument).
    #
    # Here is the basic problem: when we trace this sequence of executions
    # into an FX graph, what happens to this call sequence?  Traditionally,
    # tensor constants get interned as buffers on the FX GraphModule.  But
    # this is dangerous.  Consider:
    #
    #       x = torch.tensor(1)
    #       x.add_(2)
    #
    # Naively, this traces into:
    #
    #       t = self._tensor_constant0  # initialized to torch.tensor(1)
    #       x = torch.ops.aten.lift_fresh(t)
    #       x.add_(2)
    #
    # If lift_fresh returns t directly, the subsequent add_ call will
    # modify the tensor constant. Really, the problem is we've violated
    # the invariant the argument to lift is fresh.  So what we should
    # preserve the invariant by replacing lift_fresh with lift_fresh_copy:
    #
    #       t = self._tensor_constant0  # initialized to torch.tensor(1)
    #       x = torch.ops.aten.lift_fresh_copy(t)
    #       x.add_(2)
    #
    # This is what the overload modification does.
    if func is torch.ops.aten.lift_fresh.default:
        func = torch.ops.aten.lift_fresh_copy.default

    proxy_out = proxy_mode.tracer.create_proxy(
        "call_function",
        func,
        proxy_args,
        proxy_kwargs,
        name=proxy_mode.tracer.graph._target_to_str(func.overloadpacket.__name__),
    )

    with _enable_thunkify(proxy_mode.tracer):
        out = func(*args, **kwargs)

    # In some circumstances, we will be tracing in a situation where a tensor
    # is *statically* known to be a constant (currently, this only happens if
    # you run torch.tensor; deterministic factory functions like torch.arange
    # don't get this treatment).  When the tensor in question is small, it's
    # helpful to due constant propagation in case we call item() (in which
    # case we can return the constant value that is known, rather than give
    # an error.)  The logic here tests if constant propagation is possible
    # (because all of the inputs are constant).  If so, we disable fake tensor
    # mode (if it is on) and do true compute on the constant.
    #
    # It's worth highlighting that we're making a policy decision here.
    # There is a potential that the tensor is actually quite large, and we
    # don't actually want to run the compute.  The tensor being quite large
    # is one of the reasons why factory functions don't get this treatment
    # (since they can be quite large; if a parameter is initialized to a
    # constant value it will be!)  Similarly, there is also a potential
    # to run an operator that blows up the size of a small tensor; we don't
    # protect against this case, but we could force, e.g., only single
    # element constant computation by testing the numel of the result before
    # propagating const-ness.  Similarly, we don't require the constant to
    # live on CPU, but we could.
    any_constant = any(
        t.constant is not None
        for t in f_flat_args_kwargs
        if isinstance(t, _ProxyTensor)
    )

    constant = None

    def tensor_numel_in_limit(t: Tensor) -> bool:
        return t.numel() <= CONSTANT_NUMEL_LIMIT

    # If this is a lift, the input tensor is guaranteed to be a
    # constant, so we keep a copy of the original argument along so
    # we can query it if we're asked to item() it at some later point
    if (
        func is torch.ops.aten.lift_fresh_copy.default
        and out.numel() <= CONSTANT_NUMEL_LIMIT
    ):
        with unset_fake_temporarily():
            if not isinstance(args[0], (Proxy, Tensor)):
                raise AssertionError(f"Expected Proxy or Tensor, got {type(args[0])}")
            constant = args[0].clone()
    elif (
        torch.Tag.nondeterministic_seeded not in func.tags
        and all_constant
        and any_constant
        and pytree.tree_all_only(Tensor, tensor_numel_in_limit, out)
    ):
        # NB: do NOT include factories as constants
        with unset_fake_temporarily():
            const_flat_args_kwargs = [
                t.constant if isinstance(t, _ProxyTensor) else t
                for t in f_flat_args_kwargs
            ]
            const_args, const_kwargs = pytree.tree_unflatten(
                const_flat_args_kwargs, spec
            )
            constant = func(*const_args, **const_kwargs)
    else:
        constant = None

    track_tensor_tree(
        out,
        proxy_out,
        # pyrefly: ignore[bad-argument-type]
        constant=constant,
        tracer=tracer,
    )
    _maybe_record_pointwise_barrier(func, proxy_mode)
    return out