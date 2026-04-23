def create_fw_bw_graph(subgraph, operands, grad_outputs=None):
    with suspend_functionalization(), disable_functional_mode():
        with disable_proxy_modes_tracing():
            # args are functional tensors, generate some example tensors
            fw_inputs = pytree.tree_map(_from_fun, operands)

            from torch._guards import detect_fake_mode

            fake_mode = detect_fake_mode(fw_inputs)
            context = (
                nullcontext()
                if fake_mode is None or fake_mode.shape_env is None
                else fake_mode.shape_env.ignore_fresh_unbacked_symbols()
            )

            with context:
                fw_outs = pytree.tree_map(_from_fun, subgraph(*fw_inputs))

            num_fw_outs = len(fw_outs)

            # Collect the indexes of none in the output to check that the grad
            # is None at the corresponding index in the backward. This check is
            # performed in the autograd.Function - InvokeSubgraphAutogradOp.
            # Also collect the indexes of no_grad in the output to filter out
            # the grad_outs in the `backward` method.
            output_metadata = OutputMetadata()

            output_metadata.num_fw_outs = num_fw_outs
            for idx, fw_out in enumerate(fw_outs):
                if isinstance(fw_out, torch.SymInt):
                    output_metadata.indexes_with_symint.add(idx)
                elif not fw_out.requires_grad:
                    output_metadata.indexes_with_no_grad.add(idx)

            if grad_outputs is None:
                # Infer grad_outputs to be the same properties as the fw_outputs
                # if they're not passed in
                # Although fw_outs are equivalent to grad_outputs for tracing
                # purposes, we have to carefully handle the None and fw_out that do
                # not have require_grad. At those indexes, we will have None in the
                # backward graph.
                grad_outputs = fw_outs
                grad_outputs = [grad for grad in grad_outputs if grad is not None]
                grad_outputs = [grad for grad in grad_outputs if grad.requires_grad]

                # Force grad_out to be contiguous. This is because at runtime,
                # grad_out could have different strides than fw_outs. So, we
                # force the grad_outs to be contiguous for both tracing and
                # runtime.
                grad_outputs = [grad.contiguous() for grad in grad_outputs]

            if any(
                not isinstance(out, torch.Tensor)
                for out in grad_outputs
                if out is not None
            ):
                raise RuntimeError(
                    "Expect outputs of invoke_subgraph to only contains tensors or None. "
                    f"Got types {[type(out) for out in grad_outputs]}."
                )

            # Trace the forward subgraph
            fw_graph = _maybe_reenter_make_fx(subgraph)(*fw_inputs)

            # Trace the joint graph and assign it to the bwd graph
            bw_graph = trace_joint_graph(
                subgraph,
                fw_inputs,
                grad_outputs,
            )
            return fw_graph, bw_graph, output_metadata