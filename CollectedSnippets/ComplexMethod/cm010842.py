def apply_in_graph_mutations(
    input_info: InputAliasInfo,
    inpt_old: Tensor,
    inpt_new: Tensor,
    f_inpt: Tensor,
    input_idx: int,
    mcs: MutationCounters | None = None,
    applied_mcs: MutationCounters | None = None,
) -> None:
    if input_info.mutation_type != MutationType.MUTATED_IN_GRAPH:
        raise AssertionError(
            f"expected mutation_type MUTATED_IN_GRAPH, got {input_info.mutation_type}"
        )
    # See Note [set_() Input Mutations in AOTAutograd]
    # all mutations on the input must be under no_grad, so it is safe to put in the graph
    # Here, we're saying that if an input experienced a set call, inp.set_(other),
    # then we can effectively not have to worry about whether its data was mutated.
    # There are 3 cases:
    # (1) We mutate inp *after* the set_() call. other is a graph intermediate.
    #     In this case, we're not really mutating the input storage of "inp";
    #     we're mutating the storage of an intermdiate value (other),
    #     and slamming that storage into the input tensor. So no data mutation is necessary.
    # (2) We mutate inp *after* the set_() call. other is a graph *input*.
    #     In this case, the data mutation will be properly handled in the runtime
    #     epilogue during the processing of "other"
    # (3) We mutate inp *before* the set_() call.
    #     This case is *not* currently handled.
    if input_info.mutates_storage_metadata:
        if mcs is None or mcs.mc_storage > applied_mcs.mc_storage:  # type: ignore[union-attr]
            with torch.no_grad():
                # pyrefly: ignore [bad-argument-type, no-matching-overload]
                inpt_old.set_(inpt_new)

    # Note [Ordering of resize_() and set_()]
    # Importantly: the common usage in FSDP is that we have a dummy parameter
    # that sees a set_() and **Then** a resize_().
    # We must put those mutations into the graph in the same order,
    # Since running them in the opposite order will have different behavior.
    # We fully ban resize_() followed by set_() for now, although in principal
    # we could support this
    if input_info.mutation_inductor_storage_resize:
        if (
            mcs is None
            or mcs.mc_inductor_storage_resized > applied_mcs.mc_inductor_storage_resized  # type: ignore[union-attr]
        ):
            # resizing is not supported on subclasses (we error earlier if this happens)
            from torch._subclasses.functional_tensor import FunctionalTensor

            if not isinstance(f_inpt, FunctionalTensor):
                raise AssertionError(f"expected FunctionalTensor, got {type(f_inpt)}")
            old_storage_size = torch._functionalize_get_storage_size(  # type: ignore[attr-defined]
                f_inpt.elem, before=True
            )
            new_storage_size = torch._functionalize_get_storage_size(  # type: ignore[attr-defined]
                f_inpt.elem, before=False
            )
            if old_storage_size != new_storage_size:
                if not (old_storage_size == 0 or new_storage_size == 0):
                    raise AssertionError(f"""\
        Encosize during tracing on input {input_idx}. Old nbytes={old_storage_size}, new nbytes={new_storage_size}
        We oresizing on graph inputs as long as the input either starts or ends with a storage size of 0
        (thee for FSDP)""")
                torch.ops.inductor.resize_storage_bytes_(inpt_old, new_storage_size)
            if new_storage_size == 0:
                # Even if we marked the input as having a data mutation (thus needing a copy_()),
                # We should **ignore** it if our input has no storage
                # (this can happen if, e.g. we temporarily resize our input, copy data into it,
                #  and resize it back down to zero)
                return

    # Optimization: if the copy_() is a no-op then don't include it in the graph.
    # In theory inductor could optimize this away, however in fsdp, we end up with
    # param.copy_(param), where param is a zero-storage-size tensor,
    # and running this op in eager mode (using the aot_eager backend) will result in a segfault.
    # So we may as well optimize it away here.
    if inpt_old is inpt_new:
        # (This check needs to be done after putting resize_() in the graph,
        # since a resize_(0) doesn't actually change the FunctionalTensor's inner tensor)
        return
    # We found an input that had a (data-only) mutation.
    # Since keep_input_mutations is set, we need to faithfully apply a copy_()
    # so the compiler will see the input mutation in the graph.

    if not input_info.mutates_data:
        return

    if mcs is not None and mcs.mc_data <= applied_mcs.mc_data:  # type: ignore[union-attr]
        return

    if input_info.mutations_hidden_from_autograd:
        # Hidden from autograd = run under no_grad, **and** don't bump VC
        # (although if the tensor was created in inference mode, it has no VC)
        if inpt_old.is_inference():
            maybe_preserve_vc = nullcontext()
        else:
            maybe_preserve_vc = torch.autograd._unsafe_preserve_version_counter(
                inpt_old  # type: ignore[assignment]
            )
        with torch.no_grad(), maybe_preserve_vc:
            inpt_old.copy_(inpt_new)
    elif input_info.mutations_under_no_grad_or_inference_mode:
        # Under no_grad = run under no_grad (we still bump the VC though)
        # (inference_mode will also bump the VC, as long as the tensor in question
        # was created outside of inference_mode)

        with torch.no_grad():
            inpt_old.copy_(inpt_new)
    else:
        inpt_old.copy_(inpt_new)