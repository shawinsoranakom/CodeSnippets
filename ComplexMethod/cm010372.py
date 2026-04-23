def handle_effects(
    allow_token_discovery: bool,
    tokens: dict[_EffectType, torch.Tensor],
    op: OpType,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    """
    Args:
        allow_token_discovery: Whether or not we are discovering tokens. If this
        is true, we will create a token for every side effect type seen that
        does not have a token assigned yet.  If this is false, the tokens
        should've all been created ahead of time, so we will error if there is
        no token mapping to every effect type.

        tokens: Map of effect type to tokens. This is to chain operators of the
        same effects together so that they do not get reordered in later
        optimization passes.
    """

    # Get a token. We can't do `tokens.get(op, torch.tensor([]))` because
    # this will create an empty tensor during proxy mode tracing if the token
    # doesn't exist. But the tokens should always exist during proxy mode tracing.
    key = _get_effect(op)
    if key is None:
        raise AssertionError(f"effect key must not be None for op {op}")
    if key not in tokens:
        if not allow_token_discovery:
            raise AssertionError(
                f"Could not find a token for effect {key} which came from the function {op}"
            )
        proxy_tensor_mode = torch._C._get_dispatch_mode(
            torch._C._TorchDispatchModeKey.PROXY
        )
        if proxy_tensor_mode is not None:
            # If we discovered a new token during tracing, we are in backward.
            # Then we patch the graph, adding additional tangents_token as input to the joint graph.
            tracer = proxy_tensor_mode.tracer

            from torch.fx.experimental.proxy_tensor import (
                disable_proxy_modes_tracing,
                track_tensor_tree,
            )

            with disable_proxy_modes_tracing():
                token_tensor = new_token_tensor()

            token_proxy = proxy_tensor_mode.tracer.create_proxy(
                "placeholder", "tangents_token", (), {}, name="tangents_token"
            )
            track_tensor_tree(token_tensor, token_proxy, constant=None, tracer=tracer)

            tokens[key] = token_tensor
        else:
            tokens[key] = new_token_tensor()

    token = tokens[key]

    from torch._subclasses.functional_tensor import PythonFunctionalizeAPI

    ctx = PythonFunctionalizeAPI()

    unwrapped_token = ctx.unwrap_tensors([token])[0]
    unwrapped_args = ctx.unwrap_tensors(args)
    unwrapped_kwargs = ctx.unwrap_tensors(kwargs)  # type: ignore[arg-type]
    with ctx.redispatch_to_next():
        (new_token, *unwrapped_outs) = with_effects(
            unwrapped_token, op, *unwrapped_args, **unwrapped_kwargs
        )

    schema = _get_schema(op, unwrapped_args, unwrapped_kwargs)

    if isinstance(schema, HopSchema):
        if len(schema.returns) == 0:
            unwrapped_outs = ()
        else:
            if len(unwrapped_outs) != len(schema.returns):
                raise AssertionError(
                    f"expected {len(schema.returns)} outputs but got {len(unwrapped_outs)}"
                )
            unwrapped_outs = tuple(unwrapped_outs)
    elif len(schema.returns) == 0:
        if unwrapped_outs[0] is not None:
            raise AssertionError(f"expected no outputs but got {unwrapped_outs[0]}")
        unwrapped_outs = None  # type: ignore[assignment]
    elif len(schema.returns) == 1:
        if len(unwrapped_outs) != 1:
            raise AssertionError(f"expected 1 output but got {len(unwrapped_outs)}")
        unwrapped_outs = unwrapped_outs[0]
    else:
        if len(unwrapped_outs) != len(schema.returns):
            raise AssertionError(
                f"expected {len(schema.returns)} outputs but got {len(unwrapped_outs)}"
            )

    # Add the newly created token into the tokens map for a following call to
    # use this token.
    wrapped_token = ctx.wrap_tensors(new_token)
    if not isinstance(wrapped_token, torch.Tensor):
        raise AssertionError(
            f"expected wrapped_token to be torch.Tensor, got {type(wrapped_token)}"
        )
    tokens[key] = wrapped_token

    # pyrefly: ignore [bad-argument-type]
    return ctx.wrap_tensors(unwrapped_outs)