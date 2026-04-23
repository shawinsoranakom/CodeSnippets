def add_choices(
        cls,
        choices,
        layout,
        input_nodes,
        beta=1,
        alpha=1,
        has_bias=False,
        trans_w=False,
        input_indices=None,
        epilogue_creator: Callable[[ir.Buffer], ir.Pointwise] | None = None,
        act_mapping: dict[int, ir.IRNode] | None = None,
    ):
        """
        Add choices for the GEMM template.
        """
        # Fast path to save the epilogue calculation when x_scale/x_zp/w_scale are constant
        use_int8_fast_compensation_path = _is_int8_gemm(input_nodes) and all(
            (
                isinstance(input_nodes[idx], ir.TensorBox)
                and isinstance(input_nodes[idx].data.data, ir.ConstantBuffer)
            )
            for idx in [1, 2, 4]
        )

        if input_indices is None:
            input_indices = list(range(len(input_nodes)))

        def reorder_and_filter(inputs, layout_or_out):
            if has_bias:
                assert len(input_indices) >= 3
                # Assume the input order is [inp, x, w] and we reorder it to [x, w, inp]
                inp_idx = input_indices[0]
                x_idx = input_indices[1]
                w_idx = input_indices[2]
                return [
                    inputs[x_idx],
                    inputs[w_idx],
                    inputs[inp_idx],
                    *[inputs[idx] for idx in input_indices[3:]],
                ], layout_or_out
            elif len(inputs) >= len(input_indices):
                assert len(input_indices) >= 2
                return [inputs[idx] for idx in input_indices], layout_or_out
            else:
                # For when input is used for x and w, i.e. X@X.T or similar
                # Assumes the first input is the only input
                assert len(inputs) == 1
                return [inputs[0]] * len(input_indices), layout_or_out

        new_inputs, new_layout = reorder_and_filter(input_nodes, layout)
        is_mkldnn_wgt = (
            new_inputs[1].get_name() in V.graph.constants
            and V.graph.constants[new_inputs[1].get_name()].is_mkldnn
        )
        if is_mkldnn_wgt:
            # It shouldn't happen as viewing an mkldnn tensor, we can extend the
            # implementation if it does.
            assert not isinstance(new_inputs[1], ir.BaseView)
        # Note that the layout of MKLDNN Tensor is with the wrong stride
        view_size = new_inputs[1].layout.size
        view_stride = new_inputs[1].layout.stride
        view_offset = new_inputs[1].layout.offset

        def maybe_to_dense(inputs, layout_or_out):
            new_inputs = list(inputs)
            if isinstance(inputs[1], torch.Tensor):
                W = inputs[1]
                new_inputs[1] = W.to_dense() if W.is_mkldnn else W
            return new_inputs, layout_or_out

        def normalize_shapes(inputs, layout_or_out):
            new_inputs = list(inputs)
            if not is_mkldnn_wgt and isinstance(new_inputs[1], torch.Tensor):
                if has_free_symbols(view_size):
                    # If batch size B is dynamic, we need to set the batch size and possibly stride
                    assert not has_free_symbols(view_size[1:])
                    view_size[:] = V.graph.sizevars.guarding_hints_or_throw(view_size)
                    view_stride[:] = V.graph.sizevars.guarding_hints_or_throw(
                        view_stride
                    )
                # With the assumptation that W is the storage of unwrap view
                # thus view it back here
                new_inputs[1] = new_inputs[1].as_strided(
                    view_size, view_stride, view_offset
                )

            if not trans_w:
                return new_inputs, layout_or_out
            X = new_inputs[0]
            W = new_inputs[1]
            B = new_inputs[2] if has_bias else None
            W = transpose_w(W, trans_w)
            B = expand_bias(B, X)  # type:ignore[arg-type]
            new_inputs[1] = W
            if B is not None:
                new_inputs[2] = B
            return new_inputs, layout_or_out

        # TODO(jgong5): decide proper number of threads per problem size
        num_threads = parallel_num_threads()
        new_inputs, _ = normalize_shapes(*maybe_to_dense(new_inputs, new_layout))
        m, n, k, *_ = mm_args(
            new_inputs[0],
            new_inputs[1],
            mat2_transposed=cls.is_woq_int4(),
            use_4x2_dim=cls.is_woq_int4(),
        )
        output_dtype, compute_dtype = get_gemm_template_output_and_compute_dtype(
            new_inputs[0].get_dtype()
        )
        micro_gemm = create_micro_gemm(
            "micro_gemm",
            m,
            n,
            k,
            input_dtype=new_inputs[0].get_dtype(),
            input2_dtype=new_inputs[1].get_dtype(),
            output_dtype=output_dtype,
            compute_dtype=compute_dtype,
            alpha=alpha,
            num_threads=num_threads,
            use_ref=not cls.is_woq_int4(),
            q_group_size=cls.q_group_size(),
        )
        assert micro_gemm is not None
        pre_block_weights = cls.check_if_block_weight(new_inputs[1], micro_gemm)
        micro_gemm.use_local_vnni_blocking(not pre_block_weights)
        only_one_input = (
            input_nodes[0] == input_nodes[1] if len(input_nodes) > 1 else False
        ) and not pre_block_weights  # If weights are blocked, use the second input

        def preprocessor(inputs, layout):
            new_inputs, new_layout = normalize_shapes(
                *maybe_to_dense(*reorder_and_filter(inputs, layout))
            )
            if only_one_input and isinstance(new_inputs[0], torch.Tensor):
                return new_inputs[1:], new_layout
            return cls.prep_weight(
                new_inputs,
                new_layout,
                # pyrefly: ignore [bad-argument-type]
                micro_gemm,
                pre_block_weights,
                use_int8_fast_compensation_path,
            )

        def postprocessor(output):
            if isinstance(output, ir.TensorBox):
                # prepack the weight as input to the template buffer
                template_buffer = ir.InputsKernel.unwrap_storage_for_input(output)
                assert isinstance(template_buffer, ir.CppTemplateBuffer)
                new_input_nodes, _ = reorder_and_filter(input_nodes, layout)

                W_node = new_input_nodes[1]
                if W_node.get_name() not in V.graph.constants:
                    return output
                W = V.graph.constants[W_node.get_name()]
                new_input_nodes[1] = W
                new_input_nodes, new_layout = normalize_shapes(
                    *maybe_to_dense(new_input_nodes, layout)
                )
                new_input_nodes, _ = cls.prep_weight(
                    new_input_nodes,
                    new_layout,
                    # pyrefly: ignore [bad-argument-type]
                    micro_gemm,
                    pre_block_weights,
                    use_int8_fast_compensation_path,
                    skip_int8_compensation=True,
                )
                W_packed = new_input_nodes[1]
                W_packed_constant = V.graph.add_tensor_constant(W_packed)
                new_input_nodes[1] = W_packed_constant

                # Prune unused tensors
                prune_tensors(input_nodes, new_input_nodes)

                template_buffer.inputs[1] = ir.InputsKernel.unwrap_storage_for_input(
                    W_packed_constant
                )
            return output

        template = DataProcessorTemplateWrapper(
            cls,
            preprocessor,
            postprocessor,
            input_nodes=input_nodes,
            layout=layout,
            num_threads=num_threads,
            register_blocking=micro_gemm.register_blocking,
            beta=beta,
            alpha=alpha,
            has_bias=has_bias,
            epilogue_creator=epilogue_creator,
            should_block_weights=pre_block_weights,
            name=micro_gemm.__class__.__name__,
        )
        template.maybe_append_choice(choices)
        return template