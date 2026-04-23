def test_extract_fwd_bwd_modules_omit_aot_autograd_runtime(self):
        """Test splitting a backward graph into dI/dW subgraphs using
        omit_aot_autograd_runtime and ignore_must_be_in_fw_bw."""
        from torch._functorch.partitioners import is_sym_node

        def f(x, w):
            return ((x @ w).sum(),)

        x = torch.randn(4, 4, requires_grad=True)
        w = torch.randn(4, 4, requires_grad=True)
        joint = aot_export_joint_simple(f, [x, w], trace_joint=True)
        fw_g, bw_g = default_partition(joint, [x, w], num_fwd_outputs=1)

        # Run reference full backward
        fw_outs = fw_g(x.detach(), w.detach())
        activations = fw_outs[1:]
        grad_out = torch.ones_like(fw_outs[0])
        full_bw = bw_g(*activations, grad_out)

        # Re-partition bw_g into dI (grad_x) and dW (grad_w),
        # mimicking the split_dI_dW pattern.
        # NOTE: placeholder names are load-bearing for the partitioner —
        # _is_primal / _is_tangent classify nodes by checking substrings of
        # node.target (e.g. "tangents" in target → is_tangent). We must create
        # new placeholder nodes (not just rename) so the target is also updated.
        bw_gm = copy.deepcopy(bw_g)
        for p in list(bw_gm.graph.find_nodes(op="placeholder")):
            if p.name.startswith("tangent"):
                with bw_gm.graph.inserting_before(p):
                    new_p = bw_gm.graph.placeholder(f"not_tngnt{p.name[8:]}")
                    new_p.meta.update(p.meta)
                    p.replace_all_uses_with(new_p)
                    bw_gm.graph.erase_node(p)
        bw_gm.recompile()

        num_di = 1  # first output = grad_x
        di_outs, dw_outs, di_descs, _ = _extract_fwd_bwd_outputs(
            bw_gm, num_fwd_outputs=num_di
        )
        args = list(bw_gm.graph.find_nodes(op="placeholder"))
        di_graph = _extract_graph_with_inputs_outputs(
            bw_gm.graph,
            args,
            di_outs,
            di_descs,
            "forward",
            ignore_must_be_in_fw_bw=True,
        )
        di_names = {n.name for n in di_graph.nodes if n.op != "output"}

        saved_values = [
            n
            for n in bw_gm.graph.nodes
            if n.name in di_names
            and not is_sym_node(n)
            and "tensor_meta" in n.meta
            and any(n2.name not in di_names for n2 in n.users)
        ]

        di_mod, dw_mod = _extract_fwd_bwd_modules(
            bw_gm,
            saved_values,
            saved_sym_nodes=[],
            num_fwd_outputs=num_di,
            ignore_must_be_in_fw_bw=True,
            omit_aot_autograd_runtime=True,
        )

        # Verify graph structure
        def ph_names(gm):
            return [n.name for n in gm.graph.find_nodes(op="placeholder")]

        self.assertFalse(any(n.startswith("tangent") for n in ph_names(di_mod)))
        self.assertFalse(any(n.startswith("tangent") for n in ph_names(dw_mod)))

        # Verify numerics: dI + dW matches full backward
        bw_inputs = [*activations, grad_out]
        di_outs = di_mod(*bw_inputs)
        grad_x = di_outs[:num_di]
        dw_inputs = di_outs[num_di:]
        grad_w = dw_mod(*dw_inputs)
        if not isinstance(grad_w, (list, tuple)):
            grad_w = [grad_w]
        self.assertEqual(grad_x[0], full_bw[0])
        self.assertEqual(grad_w[0], full_bw[1])