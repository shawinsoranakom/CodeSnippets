def get_inputs(
        cls,
        choices: Sequence[ChoiceCaller],
        input_nodes: list[ir.IRNode],
        layout: ir.Layout,
        input_gen_fns: dict[int, Callable[[ir.Buffer], torch.Tensor]] | None,
        hint_override: int | None = None,
    ) -> AutotuneArgs:
        """
        Factory method to create AutotuneArgs from a list of ChoiceCallers.
        """
        if input_gen_fns is None:
            input_gen_fns = {}

        # de-duplicate args
        unique_example_inputs = {
            x.get_name(): input_gen_fns.get(
                i,
                lambda x: cls.benchmark_example_value(x, hint_override=hint_override),
                # pyrefly: ignore [bad-argument-type]
            )(x)
            for i, x in enumerate(input_nodes)
        }
        example_inputs = list(unique_example_inputs.values())
        example_inputs_extern = []

        for i, input_node in enumerate(input_nodes):
            if unique_example_inputs[input_node.get_name()].is_mkldnn:
                example_inputs_extern.append(
                    unique_example_inputs[input_node.get_name()]
                )
            else:
                base = unique_example_inputs[input_node.get_name()]
                base = base if base._base is None else base._base

                if i in input_gen_fns:
                    # Use tensor's actual shape from input_gen_fn
                    generated_tensor = unique_example_inputs[input_node.get_name()]
                    sizes = tuple(generated_tensor.size())
                    strides = tuple(generated_tensor.stride())
                    storage_offset = generated_tensor.storage_offset()
                else:
                    # Use IR node's shape resolved via size hints
                    sizes = V.graph.sizevars.optimization_hints_with_override(
                        input_node.get_size(),
                        hint_override=hint_override,
                    )
                    strides = V.graph.sizevars.optimization_hints_with_override(
                        get_strides_with_layout_constraints(input_node),
                        hint_override=hint_override,
                    )
                    storage_offset = V.graph.sizevars.optimization_hint_with_override(
                        input_node.get_layout().offset,
                        hint_override=hint_override,
                    )

                # Check if the required storage size exceeds the current storage
                # to avoid illegal memory access
                needed_size = torch._prims_common.compute_required_storage_length(
                    sizes, strides, cast(int, storage_offset)
                )
                current_size = base.untyped_storage().size()

                if needed_size > current_size:
                    # Create a new base tensor with sufficient storage
                    if base.dtype == torch.float4_e2m1fn_x2:
                        new_base = torch.randint(
                            0,
                            256,
                            (needed_size,),
                            dtype=torch.uint8,
                            device=base.device,
                        ).view(torch.float4_e2m1fn_x2)
                    else:
                        new_base = torch.randn(
                            needed_size,
                            dtype=base.dtype,
                            device=base.device,
                            requires_grad=base.requires_grad,
                        )
                    base = new_base.as_strided(
                        base.size(), base.stride(), base.storage_offset()
                    )

                example_inputs_extern.append(
                    torch.as_strided(base, sizes, strides, storage_offset)
                )
        out = cls.benchmark_example_value(layout, hint_override=hint_override)

        # Also check the output tensor for storage size
        out_base = out if out._base is None else out._base
        # Only used for benchmarking tensor setup, not correctness.
        # Offset is almost always 0; use that as fallback.
        out_offset = V.graph.sizevars.optimization_hint(layout.offset, fallback=0)
        needed_out_size = torch._prims_common.compute_required_storage_length(
            out.size(), out.stride(), out_offset
        )
        current_out_size = out_base.storage().size()

        if needed_out_size > current_out_size:
            # Create a new base tensor with sufficient storage
            if out_base.dtype == torch.float4_e2m1fn_x2:
                new_out_base = torch.randint(
                    0,
                    256,
                    (needed_out_size,),
                    dtype=torch.uint8,
                    device=out_base.device,
                ).view(torch.float4_e2m1fn_x2)
            else:
                new_out_base = torch.randn(
                    needed_out_size,
                    dtype=out_base.dtype,
                    device=out_base.device,
                    requires_grad=out_base.requires_grad,
                )
            out_base = new_out_base.as_strided(
                out_base.size(), out_base.stride(), out_base.storage_offset()
            )

        out_extern = torch.as_strided(out_base, out.size(), out.stride(), out_offset)
        expected = None
        if VERIFY:
            choices[0].benchmark(*example_inputs_extern, out=out_extern)
            expected = out_extern.clone()

        return AutotuneArgs.from_choice_args(
            example_inputs,
            example_inputs_extern,
            out,
            out_extern,
            expected,
        )