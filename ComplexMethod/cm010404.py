def flex_attention_backward_functionalize(
    ctx: torch._subclasses.functional_tensor.BaseFunctionalizeAPI,
    query: torch.Tensor,
    key: torch.Tensor,
    value: torch.Tensor,
    out: torch.Tensor,
    logsumexp: torch.Tensor,
    grad_out: torch.Tensor,
    grad_logsumexp: torch.Tensor,
    fw_graph: Callable | GraphModule,
    joint_graph: GraphModule,
    block_mask: tuple,
    scale: float,
    kernel_options: dict[str, Any],
    score_mod_other_buffers: tuple = (),
    mask_mod_other_buffers: tuple = (),
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, tuple[torch.Tensor | None, ...]]:
    """Defines the functionalization rules for the flex_attention operator.

    Write now we are unwrapping each tensor and then redispatching to the next,
    since we know that the forward score mod function is assured to be free of mutations
    to the other_buffers, we skip that mutate check and go straight to redispatching.
    """

    query_unwrapped = ctx.unwrap_tensors(query)
    key_unwrapped = ctx.unwrap_tensors(key)
    value_unwrapped = ctx.unwrap_tensors(value)
    out_unwrapped = ctx.unwrap_tensors(out)
    logsumexp_unwrapped = ctx.unwrap_tensors(logsumexp)
    grad_out_unwrapped = ctx.unwrap_tensors(grad_out)
    grad_logsumexp_unwrapped = ctx.unwrap_tensors(grad_logsumexp)
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
    if not isinstance(out_unwrapped, torch.Tensor):
        raise AssertionError(
            f"expected out_unwrapped to be torch.Tensor, got {type(out_unwrapped)}"
        )
    if not isinstance(logsumexp_unwrapped, torch.Tensor):
        raise AssertionError(
            f"expected logsumexp_unwrapped to be torch.Tensor, got {type(logsumexp_unwrapped)}"
        )
    if grad_out_unwrapped is not None and not isinstance(
        grad_out_unwrapped, torch.Tensor
    ):
        raise AssertionError(
            f"expected grad_out_unwrapped to be torch.Tensor or None, got {type(grad_out_unwrapped)}"
        )
    if grad_logsumexp_unwrapped is not None and not isinstance(
        grad_logsumexp_unwrapped, torch.Tensor
    ):
        raise AssertionError(
            f"expected grad_logsumexp_unwrapped to be torch.Tensor or None, got {type(grad_logsumexp_unwrapped)}"
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

    with ctx.redispatch_to_next():
        # pyrefly: ignore [bad-argument-type]
        functional_fw_graph = ctx.functionalize(fw_graph)
        # pyrefly: ignore [bad-argument-type]
        functional_joint_graph = ctx.functionalize(joint_graph)

        (
            grad_query,
            grad_key,
            grad_value,
            grad_score_mod_captured,
        ) = flex_attention_backward(
            query_unwrapped,
            key_unwrapped,
            value_unwrapped,
            out_unwrapped,
            logsumexp_unwrapped,
            grad_out_unwrapped,
            grad_logsumexp_unwrapped,
            functional_fw_graph,  # type: ignore[arg-type]
            functional_joint_graph,  # type: ignore[arg-type]
            block_mask_unwrapped,
            scale,
            kernel_options,
            score_mod_other_buffers_unwrapped,
            mask_mod_other_buffers_unwrapped,
        )

    return ctx.wrap_tensors((grad_query, grad_key, grad_value, grad_score_mod_captured))