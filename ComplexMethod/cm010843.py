def inner_fn(
        *args: FxValue,
    ) -> tuple[tuple[list[FxValue], list[bool]], list[AOTOutput]]:
        args_maybe_cloned = [
            maybe_to_fresh_input(i, t, meta) for i, t in enumerate(args)
        ]

        outs, outs_descs = call_and_expect_output_descs(fn, args_maybe_cloned)  # type: ignore[arg-type]
        if not isinstance(outs, (tuple, list)):
            raise AssertionError(f"expected outs to be tuple or list, got {type(outs)}")
        outs = list(outs)
        if len(meta.output_info) != len(outs):
            raise AssertionError(
                f"output_info length ({len(meta.output_info)}) != outs length ({len(outs)})"
            )

        mutated_input_pairs = [
            (x, InputMutationAOTOutput(src))
            for (i, (x, src)) in enumerate(zip(args_maybe_cloned, args_descs))
            if i in meta.mutated_inp_runtime_indices
        ]
        if mutated_input_pairs:
            mutated_inputs_to_return, mutated_inputs_to_return_descs = zip(
                *mutated_input_pairs
            )
        else:
            mutated_inputs_to_return, mutated_inputs_to_return_descs = (), ()

        intermediate_bases = []
        intermediate_bases_descs = []
        for o, info, o_desc in zip(outs, meta.output_info, outs_descs):
            if info.output_type == OutputType.alias_of_intermediate_save_as_output:
                if not isinstance(o, torch.Tensor):
                    raise AssertionError(
                        f"Expected tensor for intermediate base, got {type(o)}"
                    )
                intermediate_bases.append(o._base)
                intermediate_bases_descs.append(IntermediateBaseAOTOutput(o_desc))

        if meta.num_intermediate_bases != len(intermediate_bases):
            raise AssertionError(
                f"num_intermediate_bases ({meta.num_intermediate_bases}) != len(intermediate_bases) ({len(intermediate_bases)})"
            )

        # the compiled forward should return (mutated_inputs, user_outs, intermediate_bases)
        fw_outs_to_return = *mutated_inputs_to_return, *outs, *intermediate_bases
        fw_outs_to_return_descs = (
            *mutated_inputs_to_return_descs,
            *outs_descs,
            *intermediate_bases_descs,
        )

        # Also return a boolean mask specifying which outputs to this function will be used as tangents
        mutated_inputs_grad_mask = [
            meta.input_info[meta.mutated_inp_runtime_indices[i]].mutates_data
            and meta.input_info[meta.mutated_inp_runtime_indices[i]].requires_grad
            for (i, x) in enumerate(mutated_inputs_to_return)
        ]

        # Pass any (non-aliased) outputs in as tangents, since they'll be returned as outputs in the fw
        # For outputs that are aliases of intermediates, we will have returned the output's _base as an output in the graph instead,
        # which we *should* send to grad()
        output_grad_mask = [
            meta.output_info[i].output_type
            in [
                OutputType.non_alias,
                OutputType.unsafe_view_alias,
                OutputType.custom_function_view,
            ]
            # Also, only tensor outputs should participate in the backward
            # (in particular, Symint outputs in the forward graph shouldn't get tangents)
            and issubclass(meta.output_info[i].raw_type, Tensor)
            and meta.output_info[i].requires_grad_for_backward
            for (i, x) in enumerate(outs)
        ]

        intermediate_base_grad_mask = [True for _ in range(len(intermediate_bases))]

        out_grad_mask = (
            mutated_inputs_grad_mask + output_grad_mask + intermediate_base_grad_mask
        )
        if len(out_grad_mask) != len(fw_outs_to_return):
            raise AssertionError(
                f"out_grad_mask length ({len(out_grad_mask)}) != fw_outs_to_return length ({len(fw_outs_to_return)})"
            )

        # Take care to grab and sync the updated inputs from primals_after_cloning (the inputs we actually mutate!)
        # and not primals (the preserved inputs, pre-mutation, that we pass to grad())
        # This is annoying: our joint function needs to be aware of functionalization
        # (syncing mutated inputs before calling autograd.grad())
        # In theory, we could make the autograd engine do this automatically, although that probably isn't any cleaner.
        if not aot_config.disable_functionalization:
            for arg in args_maybe_cloned:
                if not isinstance(arg, Tensor):
                    continue
                sync_functional_tensor(arg)

        # pyrefly: ignore[bad-return]
        return (fw_outs_to_return, out_grad_mask), (
            fw_outs_to_return_descs,
            out_grad_mask,
        )