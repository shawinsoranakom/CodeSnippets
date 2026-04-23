def _(ctx, subgraph, identifier, *operands):
    from torch._higher_order_ops.auto_functionalize import (
        can_auto_functionalize,
        do_auto_functionalize_v2,
    )

    # (in the functionalization metadata phase) Capture tokens before
    tokens_before = dict(ctx.mode._tokens)

    # Check if this subgraph has effects stored in the cache
    invoke_subgraph_cache = get_invoke_subgraph_cache()
    effects = None
    if invoke_subgraph_cache:
        effects = invoke_subgraph_cache.get_effects(identifier)

    if effects:
        if len(effects) != 1:
            raise AssertionError(
                f"Multiple effects within a subgraph NYI, got {len(effects)} effects"
            )
        tokens = ctx.mode._tokens
        effects = next(iter(effects))
        token_input = tokens[effects]

        operands = (token_input, *operands)

        def wrap_subgraph(subgraph):
            def wrapped_subgraph(token, *args):
                res = subgraph(*args)
                return ctx.unwrap_tensors(ctx.mode._tokens[effects]), *res

            return wrapped_subgraph

        subgraph = wrap_subgraph(subgraph)

    unwrapped_operands = ctx.unwrap_tensors(operands)

    hop_instance = HopInstance.create(invoke_subgraph, subgraph, identifier, *operands)
    if can_auto_functionalize(hop_instance):
        # NOTE: [auto_functionalize x invoke_subgraph caching]
        # We call auto_functionalized_v2 to support input mutation of invoke_subgraph.
        # See NOTE [Support input mutation of hops] for the overall design.
        #
        # invoke_subgraph is special because of its identifier based caching mechanism.
        # In invoke_subgraph's functionalization key implementation, we create a new
        # identifier because the subgraph is replaced by FunctionWithNoFreeVars in a
        # functional + epilogue form.
        if not isinstance(identifier, str):
            raise AssertionError(
                f"identifier must be a string for auto_functionalize, got {type(identifier)}"
            )
        return do_auto_functionalize_v2(
            ctx.mode,
            hop_instance,
            (subgraph, "auto_functionalized_" + identifier, *operands),
            {},
        )

    with ctx.redispatch_to_next():
        # NB: There is an assumption that subgraph does not mutate inputs and
        # there is no aliasing. It's Dynamo's responsibility to prevent formation
        # of invoke_subgraph ops if input aliasing/mutation is detected.
        functionalized_subgraph = FunctionalizeCtxWrapper(ctx, subgraph)
        out = invoke_subgraph(functionalized_subgraph, identifier, *unwrapped_operands)

    if effects:
        (new_token, *out) = out
        ctx.mode._tokens[effects] = new_token

    # (in the functionalization metadata phase) Capture tokens after and see if
    # there are any differences (there are new effects or the token value for an
    # effect type has changed)
    tokens_after = dict(ctx.mode._tokens)
    discovered_effects = set()
    for effect_type, token in tokens_after.items():
        if effect_type not in tokens_before or tokens_before[effect_type] is not token:
            discovered_effects.add(effect_type)

    if discovered_effects:
        if not ctx.mode._allow_token_discovery:
            raise AssertionError(
                f"Number of tokens changed by {len(discovered_effects)} when tracing subgraph {subgraph}."
            )
        # Store discovered effects in the cache by identifier
        if invoke_subgraph_cache:
            invoke_subgraph_cache.add_effects(identifier, discovered_effects)

    return ctx.wrap_tensors(out)