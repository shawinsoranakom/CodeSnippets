def flex_attention_functionalize(
    ctx: torch._subclasses.functional_tensor.BaseFunctionalizeAPI,
    query: torch.Tensor,
    key: torch.Tensor,
    value: torch.Tensor,
    score_mod: Callable,
    block_mask: tuple,
    scale: float,
    kernel_options: dict[str, Any],
    score_mod_other_buffers: tuple = (),
    mask_mod_other_buffers: tuple = (),
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Defines the functionalization rules for the flex_attention operator.

    Write now we are unwrapping each tensor and then redispatching to the next, however we want to
    guard against any mutations in the score_mod function, to the other_buffers since those
    are free variables.
    """
    from torch._dynamo._trace_wrapped_higher_order_op import TransformGetItemToIndex

    query_unwrapped = ctx.unwrap_tensors(query)
    key_unwrapped = ctx.unwrap_tensors(key)
    value_unwrapped = ctx.unwrap_tensors(value)
    block_mask_unwrapped = ctx.unwrap_tensors(block_mask)
    score_mod_other_buffers_unwrapped = ctx.unwrap_tensors(score_mod_other_buffers)
    mask_mod_other_buffers_unwrapped = ctx.unwrap_tensors(mask_mod_other_buffers)

    # Appease the mypy overlords
    if not isinstance(query_unwrapped, torch.Tensor):
        raise AssertionError(
            f"expected query_unwrapped to be torch.Tensor, got {type(query_unwrapped)}"
        )
    if not isinstance(key_unwrapped, torch.Tensor):
        raise AssertionError(
            f"expected key_unwrapped to be torch.Tensor, got {type(key_unwrapped)}"
        )
    if not isinstance(value_unwrapped, torch.Tensor):
        raise AssertionError(
            f"expected value_unwrapped to be torch.Tensor, got {type(value_unwrapped)}"
        )
    if not isinstance(block_mask_unwrapped, tuple):
        raise AssertionError(
            f"expected block_mask_unwrapped to be tuple, got {type(block_mask_unwrapped)}"
        )
    if not isinstance(score_mod_other_buffers_unwrapped, tuple):
        raise AssertionError(
            f"expected score_mod_other_buffers_unwrapped to be tuple, got {type(score_mod_other_buffers_unwrapped)}"
        )
    if not isinstance(mask_mod_other_buffers_unwrapped, tuple):
        raise AssertionError(
            f"expected mask_mod_other_buffers_unwrapped to be tuple, got {type(mask_mod_other_buffers_unwrapped)}"
        )

    example_vals = (
        [query_unwrapped.new_zeros(())]
        + [query_unwrapped.new_zeros((), dtype=torch.int) for _ in range(4)]
        + list(score_mod_other_buffers_unwrapped)
    )
    with ctx.redispatch_to_next():
        functional_score_mod = ctx.functionalize(score_mod)
        pre_dispatch = hasattr(ctx, "mode") and ctx.mode.pre_dispatch
        with TransformGetItemToIndex():
            # TODO: So far only the input mutations are checked
            # In the other HOPs, also aliases are checked which is
            # omitted here
            mutates = _has_potential_branch_input_mutation(
                score_mod, example_vals, pre_dispatch
            )
        # The only care about mutations of existing buffers since we can't replay these.
        # However, we can just error if anything is detected
        if mutates:
            raise UnsupportedAliasMutationException("Mutations detected in score_mod")

        out = flex_attention(
            query_unwrapped,
            key_unwrapped,
            value_unwrapped,
            functional_score_mod,
            block_mask_unwrapped,
            scale,
            kernel_options,
            score_mod_other_buffers_unwrapped,
            mask_mod_other_buffers_unwrapped,
        )
    return ctx.wrap_tensors(out)