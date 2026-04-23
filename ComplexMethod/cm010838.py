def wrap_tensor_subclasses(
    unwrapped_args: Sequence[Any],
    *,
    subclass_metas: list[PlainTensorMeta | SubclassCreationMeta],
    num_fw_outs_saved_for_bw: int | None = None,
    included_subclass_symints: bool = False,
    is_runtime: bool = False,
    make_subclass_override: Callable[..., Any] | None = None,
) -> tuple[Any, ...]:
    # pyrefly: ignore [implicit-any]
    wrapped_args = []
    num_args_tallied = 0
    for subclass_meta in subclass_metas:
        if isinstance(subclass_meta, PlainTensorMeta):
            wrapped_args.append(unwrapped_args[subclass_meta.unwrapped_idx])
            num_args_tallied += 1
        else:
            if not isinstance(subclass_meta, SubclassCreationMeta):
                raise AssertionError(
                    f"expected SubclassCreationMeta, got {type(subclass_meta)}"
                )
            if subclass_meta.included_subclass_symints != included_subclass_symints:
                raise AssertionError(
                    f"included_subclass_symints mismatch: {subclass_meta.included_subclass_symints} != {included_subclass_symints}"
                )

            if make_subclass_override:
                wrapped_args.append(
                    make_subclass_override(subclass_meta, is_runtime, unwrapped_args)
                )
            else:
                wrapped_args.append(
                    subclass_meta.creation_fn(
                        unwrapped_args,
                        is_runtime=is_runtime,
                    )
                )
            num_args_tallied += subclass_meta.arg_count

    # Note: [Partitioner handling for Subclasses, Part 2]
    # At the beginning of AOTAutograd, we collect metadata on the inputs and outputs of the user fw,
    # to figure out which inputs/outputs are subclasses, and how to reconstruct the subclasses after flattening them.
    #
    # When this function is called at runtime in the forward,
    # we have been passed a list of (flattened) dense-tensor fw-outs, and need to reconstruct any subclass fw outs.
    #
    # One reasonable question that you should ask: when should the dense_tensor -> subclass_tensor wrapping happen?
    # Answer: we do it **inside of our compiled autograd.Function**.
    # This seems like morally the right place: autograd happens above subclass desugaring,
    # so autograd should see actual tensor subclasses at runtime, and not flattened dense tensors.
    #
    # This causes a tricky interaction though: when we run the min-cut partitioner to divvy up the joint graph
    # into a forward and backward graph, we end up with some activations that show up as extra outputs
    # in the compiled forward graph, that are **not** user outputs.
    # These activations are not visible to the user, and so there's no need for us to wrap them back into subclasses.
    #
    # On top of that, when we first computed subclass metadata (in `run_functionalized_fw_and_collect_metadata`),
    # we computed subclass metadata on every forward output, but this did **not** include activations
    # created by the partitioner.
    # as a result, `unwrapped_args` here will correspond to (*unwrapped_user_fw_outs, *activations),
    # but `subclass_metas` will only correspond to subclass metadata on `user_fw_outs`.
    # We then need to make sure that we return (*wrapped_user_fw_outs, *activations).
    if num_fw_outs_saved_for_bw is not None:
        if len(unwrapped_args) != num_args_tallied + num_fw_outs_saved_for_bw:
            raise AssertionError(
                f"Expected the number actual unwrapped-subclass outputs {len(unwrapped_args)} to equal "
                f"the number of args calculated from subclasses ({num_args_tallied}) plus the number of "
                f"additional activations saved for the backward pass ({num_fw_outs_saved_for_bw})"
            )
        activations = unwrapped_args[num_args_tallied:]
        if isinstance(wrapped_args, tuple) and isinstance(activations, tuple):
            return wrapped_args + activations
        return tuple(list(wrapped_args) + list(activations))
    else:
        if len(unwrapped_args) != num_args_tallied:
            raise AssertionError(
                f"Expected {len(unwrapped_args)} == {num_args_tallied}"
            )
        return tuple(wrapped_args)