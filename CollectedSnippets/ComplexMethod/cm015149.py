def indiv_variant_test_jit(
        self, device, dtype, op, sample, func_type, variant, has_fake_function
    ):
        _requires_grad = dtype in op.supported_backward_dtypes(
            torch.device(device).type
        )
        support_script = op.supports_scripting
        # Create accessor for script function variant
        name = op.name + "_" if func_type == "inplace" else op.name

        # run with disable_autodiff_subgraph_inlining(True) to test
        #   autodiff support. Context manager forces the graph to contain
        #   DifferentiableGraph nodes if they are present
        with disable_autodiff_subgraph_inlining():
            # Check scripted forward, grad, and grad grad
            if support_script:
                script_fn = create_script_fn(self, name, func_type)

            def out_fn(output):
                # Processes the output for autograd
                if sample.output_process_fn_grad is not None:
                    return sample.output_process_fn_grad(output)
                return output

            def get_sample():
                return (
                    clone_input_helper(sample.input)
                    if op.name[-1] == "_"
                    else sample.input
                )

            if support_script:
                check_against_reference(
                    self,
                    script_fn,
                    op.get_op(),
                    out_fn,
                    (get_sample(),) + sample.args,
                    sample.kwargs,
                    no_grad=not _requires_grad,
                    no_gradgrad=not op.supports_gradgrad,
                )

            # Check traced forward, grad, and grad grad
            # TODO: fix tracing here
            supports_tracing = op.supports_tracing and not has_fake_function
            if op.assert_jit_shape_analysis:
                self.assertTrue(supports_tracing)

            if supports_tracing:
                traced_fn = create_traced_fn(self, variant)
                check_against_reference(
                    self,
                    traced_fn,
                    op.get_op(),
                    out_fn,
                    (get_sample(),) + sample.args,
                    sample.kwargs,
                    no_grad=not _requires_grad,
                    no_gradgrad=not op.supports_gradgrad,
                )

            # Check alias annotation schema for correctness (make
            #   sure inputs that aren't supposed to be modified aren't)
            # Note: only runs in float32 because schema isn't affected by dtype,
            #   so running it on all dtypes is would be excessive
            if dtype == torch.float32:
                # TODO: no reason why we can't run this with tracing graph
                if support_script and op.name != "rsub":
                    check_alias_annotation(
                        name,
                        (get_sample(),) + sample.args,
                        sample.kwargs,
                        func_type=func_type,
                        aten_name=op.aten_name,
                    )

                # TODO: use script graph as well
                checked_shape_analysis = False
                if supports_tracing:
                    out = variant(get_sample(), *sample.args, **sample.kwargs)

                    # right now, tuple of outputs and tensor output supported
                    # TODO: list of tensor outputs
                    tuple_of_tensors = isinstance(out, tuple) and all(
                        isinstance(elem, torch.Tensor) for elem in out
                    )

                    if isinstance(out, torch.Tensor) or tuple_of_tensors:
                        if tuple_of_tensors:
                            sizes = [elem.size() for elem in out]
                        else:
                            sizes = out.size()
                        self.checkShapeAnalysis(
                            sizes, traced_fn.graph, op.assert_jit_shape_analysis
                        )
                        checked_shape_analysis = True
                if op.assert_jit_shape_analysis:
                    self.assertTrue(checked_shape_analysis)

            # Check autodifferentiation of nodes for traced and scripted graphs, only need to check once per sample
            if dtype is torch.float32:
                # Sandcastle doesn't fuse nodes
                if IS_SANDCASTLE:
                    # fusible nodes are expected to be found in FusionGroups in the DifferentiableGraphs
                    nonfusible_nodes = (
                        op.autodiff_nonfusible_nodes + op.autodiff_fusible_nodes
                    )
                    fusible_nodes = []
                else:
                    nonfusible_nodes = op.autodiff_nonfusible_nodes
                    fusible_nodes = op.autodiff_fusible_nodes

                if supports_tracing:
                    self.assertAutodiffNode(
                        traced_fn.last_graph,
                        op.assert_autodiffed,
                        nonfusible_nodes,
                        fusible_nodes,
                    )
                if support_script:
                    self.assertAutodiffNode(
                        script_fn.last_graph,
                        op.assert_autodiffed,
                        nonfusible_nodes,
                        fusible_nodes,
                    )