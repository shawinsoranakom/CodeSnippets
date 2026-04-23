def compute_overlapping_inputs(
    aot_config: AOTConfig, fwd_inputs: list[Any], aliased_input_indices: list[int]
) -> set[int]:
    num_aliases = len(aliased_input_indices)

    shape_env = None
    maybe_suppress_guards = contextlib.nullcontext
    tracing_context = torch._guards.TracingContext.try_get()

    if tracing_context is not None:
        if tracing_context.fake_mode is None:
            raise AssertionError("tracing_context.fake_mode must not be None")
        shape_env = tracing_context.fake_mode.shape_env

        # Check whether we can actually get the dynamo sources from within AOTAutograd.
        if aot_config.aot_autograd_arg_pos_to_source and shape_env is not None:
            maybe_suppress_guards = shape_env.suppress_guards  # type: ignore[assignment]

    # Check whether there are any symbolic values being used.
    # We do this for 2 reasons:
    #   1. StorageOverlap guard is only issued whenever dynamic shapes is turned on
    #   2. Triggers the fast-path for computing storage overlapping
    symbolic = any(
        isinstance(x, torch.SymInt)
        for i in aliased_input_indices
        for x in [
            *fwd_inputs[i].shape,
            *fwd_inputs[i].stride(),
            fwd_inputs[i].storage_offset(),
        ]
    )

    if torch._inductor.config.is_fbcode():
        if symbolic and num_aliases > 400:
            from torch._subclasses.fake_tensor import (
                UnsupportedMutationAliasingException,
            )
            from torch._utils_internal import justknobs_check

            msg = f"Encountered {num_aliases} dynamic, aliased/mutated inputs, consider setting dynamic=False"

            if justknobs_check(
                "pytorch/compiler:aliased_inputs_with_mutation_and_dyn_shapes_killswitch",
                False,
            ):
                raise UnsupportedMutationAliasingException(msg)

    with maybe_suppress_guards():
        aliased_fwd_inputs = [fwd_inputs[i] for i in aliased_input_indices]
        actual_aliased_indices = {
            aliased_input_indices[i]
            for i in compute_overlapping_tensors(aliased_fwd_inputs, symbolic=symbolic)
        }

    # Add the StorageOverlap AOTAutograd guard only if we are actually keeping track of
    # dynamo sources inside AOTAutograd.
    if (
        tracing_context is not None
        # Make sure dynamic shapes is currently being used.
        and symbolic
        # We check that we have more than 1 aliased tensor, which should be true at
        # this point, anyway.
        and num_aliases > 1
        and aot_config.aot_autograd_arg_pos_to_source
    ):
        no_overlap_indices = list(set(aliased_input_indices) - actual_aliased_indices)

        overlapping_sources = [
            aot_config.aot_autograd_arg_pos_to_source[i] for i in actual_aliased_indices
        ]
        non_overlapping_sources = [
            aot_config.aot_autograd_arg_pos_to_source[i] for i in no_overlap_indices
        ]

        tracing_context.guards_context.aotautograd_guards.append(
            StorageOverlap(overlapping_sources, non_overlapping_sources)
        )

    return actual_aliased_indices