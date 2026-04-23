def forward(
        ctx,
        cond_fn,
        body_fn,
        num_carried_inputs,
        num_additional_inputs,
        *carries_and_inputs,
    ):
        from torch._higher_order_ops.scan import split_into_chunks

        carries, additional_inputs = split_into_chunks(
            carries_and_inputs, [num_carried_inputs, num_additional_inputs]
        )
        with torch._C._AutoDispatchBelowAutograd():
            fw_outputs = while_loop_stack_output_op(
                cond_fn, body_fn, carries, additional_inputs
            )

        if hasattr(ctx, "fw_cond_fn"):
            raise AssertionError("ctx already has fw_cond_fn attribute")
        if hasattr(ctx, "fw_body_fn"):
            raise AssertionError("ctx already has fw_body_fn attribute")
        if hasattr(ctx, "carries"):
            raise AssertionError("ctx already has carries attribute")
        if hasattr(ctx, "additional_inputs"):
            raise AssertionError("ctx already has additional_inputs attribute")
        if hasattr(ctx, "fw_outputs"):
            raise AssertionError("ctx already has fw_outputs attribute")
        ctx.fw_cond_fn = cond_fn
        ctx.fw_body_fn = body_fn
        ctx.carries = carries
        ctx.additional_inputs = additional_inputs
        ctx.fw_outputs = fw_outputs
        loop_count = None
        # pyrefly: ignore [bad-assignment]
        for out in fw_outputs:
            if isinstance(out, torch.Tensor):
                if loop_count is not None:
                    if out.size(0) != loop_count:
                        raise AssertionError(
                            f"inconsistent loop_count: expected {loop_count}, got {out.size(0)}"
                        )
                else:
                    loop_count = out.size(0)
        if loop_count is None:
            raise AssertionError(
                "loop_count must not be None after processing fw_outputs"
            )

        # Remove the loop_count from pending_fresh_unbacked_symbols
        # because it's not part of forward output and it's impossible
        # to bind it to a proxy in forward graph anyways.
        if (
            isinstance(loop_count, torch.SymInt)
            and (shape_env := loop_count.node.shape_env)
            and loop_count in shape_env.pending_fresh_unbacked_symbols
        ):
            shape_env.pending_fresh_unbacked_symbols.remove(loop_count)

        # Even when body function is not executed, we clone and unsqueeze the input
        # to avoid the aliasing, therefore loop_count is always >= 1
        torch._check(loop_count >= 1)
        # We snapshot the dispatch keys in forward for materializing the
        # the bw_graph in backward.
        ctx._fw_include_key_set = torch._C._dispatch_tls_local_include_set()
        ctx._fw_exclude_key_set = torch._C._dispatch_tls_local_exclude_set()
        if len(fw_outputs) <= 0:
            raise AssertionError("fw_outputs shouldn't be empty")
        # Only the last of the output fw_outputs need to be returned
        return tuple(ckp[-1] for ckp in fw_outputs)