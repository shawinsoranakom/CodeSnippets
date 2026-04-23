def _call_function(
        self,
        tx: "InstructionTranslator",
        args: Sequence[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker:
        from .builder import wrap_fx_proxy

        if len(args) != 14:
            return self._call_function_fallback(tx, args, kwargs)

        (
            query,
            key,
            value,
            out,
            logsumexp,
            grad_out,
            grad_logsumexp,
            fw_graph,
            joint_graph,
            block_mask,
            scale,
            kernel_options,
            score_mod_other_buffers,
            mask_mod_other_buffers,
        ) = args

        if (
            not isinstance(block_mask, TupleVariable)
            or not isinstance(score_mod_other_buffers, TupleVariable)
            or not isinstance(mask_mod_other_buffers, TupleVariable)
            or len(block_mask.items) < 1
        ):
            return self._call_function_fallback(tx, args, kwargs)

        if self._uses_pretraced_graphs(fw_graph, joint_graph):
            return self._call_function_fallback(tx, args, kwargs)

        fw_graph_node, fw_graph_lifted_args, fw_graph_gm = self.create_wrapped_node(
            tx, query, fw_graph, "score_mod", score_mod_other_buffers.items
        )

        joint_graph_node = self._derive_joint_graph(
            tx,
            query,
            fw_graph_gm,
            score_mod_other_buffers,
            fw_graph_lifted_args,
        )

        mask_fn = block_mask.items[-1]
        if mask_fn.is_python_constant() and mask_fn.as_python_constant() is None:
            mask_fn = VariableTracker.build(
                tx,
                torch.nn.attention.flex_attention.noop_mask,
                source=mask_fn.source,
            )
        mask_fn_node, mask_fn_lifted_args, _ = self.create_wrapped_node(
            tx, query, mask_fn, "mask_fn", mask_mod_other_buffers.items
        )

        proxied_args = [
            query,
            key,
            value,
            out,
            logsumexp,
            grad_out,
            grad_logsumexp,
            TupleVariable(block_mask.items[:-1], source=block_mask.source),
            scale,
            kernel_options,
        ]
        inp_args, _ = proxy_args_kwargs(proxied_args, {})
        proxied_score_mod_other_buffers = tuple(
            self.to_proxy(tx, arg) for arg in score_mod_other_buffers.items
        )
        proxied_mask_mod_other_buffers = tuple(
            self.to_proxy(tx, arg) for arg in mask_mod_other_buffers.items
        )

        (
            inp_q,
            inp_k,
            inp_v,
            inp_out,
            inp_lse,
            inp_grad_out,
            inp_grad_lse,
            inp_block_mask,
            inp_scale,
            inp_kernel_options,
        ) = inp_args

        block_mask_proxy = tuple(inp_block_mask + (mask_fn_node,))

        with torch.fx.experimental.proxy_tensor.set_original_aten_op(self.value):
            return wrap_fx_proxy(
                tx=tx,
                proxy=tx.output.create_proxy(
                    "call_function",
                    self.value,
                    args=(
                        inp_q,
                        inp_k,
                        inp_v,
                        inp_out,
                        inp_lse,
                        inp_grad_out,
                        inp_grad_lse,
                        fw_graph_node,
                        joint_graph_node,
                        block_mask_proxy,
                        inp_scale,
                        inp_kernel_options,
                        proxied_score_mod_other_buffers + fw_graph_lifted_args,
                        proxied_mask_mod_other_buffers + mask_fn_lifted_args,
                    ),
                    kwargs={},
                ),
                example_value=None,
            )