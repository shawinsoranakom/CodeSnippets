def backward(ctx, *grads):
        from torch._higher_order_ops.cond import create_bw_fn
        from torch._higher_order_ops.scan import split_into_chunks

        # set up single step bw fn
        bw_body_fn = create_bw_fn(ctx.fw_body_fn, ctx.carries + ctx.additional_inputs)
        # Note [Handle inputs that're not differentiable]
        # When a forward input is non-differentiable e.g. a symint or an integer tensor, their gradients
        # will be None. However, we don't want to return None in the subgraph because this complicates the
        # inductor codegen, where we need to do a non-uniform treatment for None and tensors.
        # So we set up masks and filter the None gradients so that only tensors are returned from each step.
        carries_tensor_masks = [
            bool(isinstance(t, torch.Tensor) and t.dtype.is_floating_point)
            for t in ctx.carries
        ]
        additional_inputs_tensor_masks = [
            bool(isinstance(t, torch.Tensor) and t.dtype.is_floating_point)
            for t in ctx.additional_inputs
        ]

        init_idx = torch.zeros((), dtype=torch.int64)
        init_grad_carries = filter_with_masks(grads, carries_tensor_masks)  # type: ignore[arg-type]
        init_grad_additional_inputs = tuple(
            torch.zeros_like(t)
            for need_keep, t in zip(
                additional_inputs_tensor_masks, ctx.additional_inputs
            )
            if need_keep
        )
        # We need to the forward inputs to each iteration to compute the backward
        # which is the concatenation of first iteraiton input i.e. ctx.carries and all iterations's
        # output except the last iteration.
        fw_carries = [
            torch.cat([carry.unsqueeze(0), carries[:-1]])
            for carry, carries in zip(ctx.carries, ctx.fw_outputs)
        ]
        for fw_carry, carry in zip(fw_carries, ctx.carries):
            fw_carry.requires_grad_(carry.requires_grad)

        _, spec = pytree.tree_flatten(
            (
                init_idx,
                init_grad_carries,
                init_grad_additional_inputs,
                ctx.fw_outputs,
                ctx.additional_inputs,
            )
        )

        def cond_fn(*flat_args):
            (
                idx,
                grad_carries,
                grad_additional_inputs,
                fw_carries,
                additional_inputs,
            ) = pytree.tree_unflatten(flat_args, spec)
            if not isinstance(fw_carries[0], torch.Tensor):
                raise AssertionError(
                    f"expected fw_carries[0] to be torch.Tensor, got {type(fw_carries[0])}"
                )
            # excluding the last iteration's output
            return idx < fw_carries[0].size(0)

        def body_fn(*flat_args):
            (
                idx,
                grad_carries,
                grad_additional_inputs,
                fw_carries,
                additional_inputs,
            ) = pytree.tree_unflatten(flat_args, spec)
            reversed_idx = fw_carries[0].size(0) - idx - 1
            selected_fw_carries = [
                ckp.select(0, reversed_idx.item()) for ckp in fw_carries
            ]
            cur_grad_carries, cur_grad_additional_inputs = split_into_chunks(
                bw_body_fn(*selected_fw_carries, *additional_inputs, *grad_carries),
                [len(ctx.carries), len(ctx.additional_inputs)],
            )
            if not all(isinstance(t, torch.Tensor) for t in cur_grad_carries):
                raise AssertionError(
                    f"all cur_grad_carries must be tensors, got {[type(t) for t in cur_grad_carries]}"
                )
            cur_grad_carries_tensors = filter_with_masks(
                cur_grad_carries, carries_tensor_masks
            )
            cur_grad_additional_inputs_tensors = filter_with_masks(
                cur_grad_additional_inputs, additional_inputs_tensor_masks
            )
            return (
                idx + 1,
                *cur_grad_carries_tensors,
                *(
                    cur_grad + grad
                    for cur_grad, grad in zip(
                        cur_grad_additional_inputs_tensors, grad_additional_inputs
                    )
                ),
            )

        args_single_step_bw = (
            init_idx,
            *init_grad_carries,
            *init_grad_additional_inputs,
            *fw_carries,
            *ctx.additional_inputs,
        )

        cond_gm = materialize_as_graph(
            cond_fn,
            args_single_step_bw,
            ctx._fw_include_key_set,
            ctx._fw_exclude_key_set,
            force_enable_grad=True,
        )

        body_gm = materialize_as_graph(
            body_fn,
            args_single_step_bw,
            ctx._fw_include_key_set,
            ctx._fw_exclude_key_set,
            force_enable_grad=True,
        )

        _, final_grad_carries, final_grad_additional_inputs = split_into_chunks(
            while_loop_op(
                # pyrefly: ignore [bad-argument-type]
                cond_gm,
                # pyrefly: ignore [bad-argument-type]
                body_gm,
                # pyrefly: ignore [bad-argument-type]
                (
                    init_idx,
                    *init_grad_carries,
                    *init_grad_additional_inputs,
                ),
                (*fw_carries, *ctx.additional_inputs),
            ),
            [1, len(init_grad_carries), len(init_grad_additional_inputs)],
        )
        return (
            None,
            None,
            None,
            None,
            *fill_none_with_masks(final_grad_carries, carries_tensor_masks),
            *fill_none_with_masks(
                final_grad_additional_inputs, additional_inputs_tensor_masks
            ),
        )