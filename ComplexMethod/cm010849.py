def merge_view_inputs(
    aot_config: AOTConfig,
    fwd_inputs: list[Any],
    # This is None when called at runtime from post_compile closure
    fwd_inputs_descs: list[AOTInput] | None,
    mutated_input_info: list[InputAliasInfo],
    *,
    # The autograd case currently has more restrictions than the inference case.
    is_inference: bool,
) -> tuple[list[Any], list[AOTInput], list[int | tuple[int, torch.Tensor]] | None]:
    if fwd_inputs_descs is None:
        fwd_inputs_descs = [DummyAOTInput(i) for i in range(len(fwd_inputs))]

    def _are_differentiable_views(view1: torch.Tensor, view2: torch.Tensor) -> bool:
        if view1 is view2:
            return True
        if view1._base is None and view2._base is None:
            return False
        if view1._base is view2._base or view1._base is view2 or view1 is view2._base:
            return True
        return False

    def _same_dtype_views(view1: torch.Tensor, view2: torch.Tensor) -> bool:
        if view1.dtype != view2.dtype:
            return False
        if view1._base is not None and view1.dtype != view1._base.dtype:
            return False
        if view2._base is not None and view2.dtype != view2._base.dtype:
            return False
        return True

    if len(fwd_inputs) != len(mutated_input_info):
        raise AssertionError(
            f"expected len(fwd_inputs) == len(mutated_input_info), "
            f"got {len(fwd_inputs)} != {len(mutated_input_info)}"
        )
    if not [info for info in mutated_input_info if info.mutates_data]:
        # Return early when there are no mutations.
        return fwd_inputs, fwd_inputs_descs, None

    storage_ref_to_idx: dict[StorageWeakRef, list[int]] = collections.defaultdict(list)
    # pyrefly: ignore [implicit-any]
    base_args = []
    # pyrefly: ignore [implicit-any]
    other_args = []
    base_args_descs = []
    other_args_descs = []
    for i, (inpt, source) in enumerate(zip(fwd_inputs, fwd_inputs_descs)):
        if isinstance(inpt, Tensor):
            storage_ref = StorageWeakRef(inpt.untyped_storage())
            storage_ref_to_idx[storage_ref].append(i)
        else:
            other_args.append(inpt)
            other_args_descs.append(source)
    # Note [Synthetic Base Info Metadata]
    # This list contains metadata that tells you what the i'th argument in the inner calling convention should be.
    # It's either:
    # - another int (corresponding to the index in the argument list of the element from the outer calling convention)
    # - idx, view_tensor, where we can generate the new output with view_tensor._view_func(old_args[idx])
    #   idx corresponds to which synthetic base from the outer calling context to view
    inner_calling_convention_meta: dict[int, int | tuple[int, torch.Tensor]] = {}
    for aliased_input_indices in storage_ref_to_idx.values():
        if len(aliased_input_indices) <= 1 or not any(
            # We only care about mutations that affect all aliases,
            # so metadata mutations on an input doesn't require us to do synthetic base handling.
            mutated_input_info[inpt_idx].mutates_data
            for inpt_idx in aliased_input_indices
        ):
            other_args.extend(
                fwd_inputs[curr_idx] for curr_idx in aliased_input_indices
            )
            other_args_descs.extend(
                fwd_inputs_descs[curr_idx] for curr_idx in aliased_input_indices
            )
            continue

        # Here, we attempt to do a more complicated check to detect false aliasing
        # (e.g. if all the tensors have the same storage, but don't actually overlap)
        # In theory, we could have a large group of tensors that all share storages, where only *some* of them
        # have overlapping memory.
        # I don't bother with that case for now: here, we only bail out earlier if we detect that **every** pair
        # of tensors in the current group that shares a storage is non-overlapping.
        aliased_input_indices_no_false_sharing = compute_overlapping_inputs(
            aot_config, fwd_inputs, aliased_input_indices
        )
        if len(aliased_input_indices_no_false_sharing) <= 1:
            other_args.extend(
                fwd_inputs[curr_idx] for curr_idx in aliased_input_indices
            )
            other_args_descs.extend(
                fwd_inputs_descs[curr_idx] for curr_idx in aliased_input_indices
            )
            continue

        # We detected an input that was mutated, AND aliases with another input.
        # we need to replace this set of aliased inputs with a single synthetic base.
        # For now, I'm banning a bunch of cases. We expect dynamo to properly detect these cases
        # and error out. We can fix them later.
        # These checks are transitive, so we don't need to check every pair.
        for idx1, idx2 in zip(
            aliased_input_indices, aliased_input_indices[1:], strict=False
        ):
            view1 = fwd_inputs[idx1]
            view2 = fwd_inputs[idx2]
            # The "inputs that are aliased but have different differentiable bases" case
            # is more complicated and hopefully pretty rare. Not currently handled.
            if not is_inference:
                if not _are_differentiable_views(view1, view2):
                    raise AssertionError(
                        "aot_autograd() does not yet handle non-differentiable view input mutations."
                    )
            # Regenerating views when reinterpreting complex / real tensors seems non-trivial,
            # not handling for now
            if not _same_dtype_views(view1, view2):
                raise AssertionError(
                    "aot_autograd() does not yet handle input mutations on views with different dtypes."
                )
        non_none_bases = [
            (i, fwd_inputs[i]._base)
            for i in aliased_input_indices
            if fwd_inputs[i]._base is not None
        ]
        aliases_with_none_bases = [
            fwd_inputs[i] for i in aliased_input_indices if fwd_inputs[i]._base is None
        ]
        synthetic_base_desc: AOTInput
        if len(non_none_bases) == 0:
            # Case where none of the aliases have a ._base
            # we generate a synthetic base without gradients, and generate views off of it
            # We hit this case when we have input tensors to the graph that share a storage,
            # but do not have a ._base field.
            # Wondering when we hit this case?
            # The _base field simply says that autograd knows about the aliasing relationship,
            # but sometimes we create tensors which are aliased out of the same storage but guaranteed
            # to be disjoint. In these cases, we will skip setting up the _base relationship
            # for performance reasons (because the fact that the tensors share the same storage
            # is unobservable unless you (1) do naughty things with resize_/as_strided
            # or (2) look at the storage--as we are doing here.)
            # One particular example of this is optimizer steps on the LSTM module:
            # LSTM parameters are packed into a contiguous storage for efficiency reasons when
            # calling cuDNN kernels, so when these parameters get passed to the optimizer we will
            # find they share the same storage, but do not have _base set since they are all disjoint.
            #
            # NOTE: There is one case where this is unsafe:
            # torch.Tensor(storage) will ALWAYS create a 1D tensor, which is not necessarily
            # the same shape as the "actual" base that the tensor came from.
            # For the most part this is fine, because we always use as_strided()
            # to generate the original aliased inputs again.
            # If we were to use view-replay though, this could cause the aliased views
            # to have incorrect sizes.
            example_idx = aliased_input_indices[0]
            example_alias = fwd_inputs[example_idx]
            # Note that this function is reused at both trace time and runtime.
            # At trace time, we're under a FakeMode so synthetic_base becomes a FakeTensor.
            synthetic_base = torch.empty(
                (0,), dtype=example_alias.dtype, device=example_alias.device
            )
            # We don't actually have a convenient way of going from storage -> tensor,
            # So using set_() here (we suffer some minor overhead, but this case is rare).
            synthetic_base.set_(example_alias.untyped_storage())
            synthetic_base_desc = SyntheticBaseAOTInput(fwd_inputs_descs[example_idx])
        else:
            # Case where all of the aliases require gradients, and have the same _base.
            i, synthetic_base = non_none_bases[0]
            synthetic_base_desc = ViewBaseAOTInput(fwd_inputs_descs[i])
            for _, other_base in non_none_bases[1:]:
                if other_base is not synthetic_base:
                    raise AssertionError(
                        "aot_autograd() does not yet handle non-differentiable view input mutations."
                    )
            for alias in aliases_with_none_bases:
                if alias is not synthetic_base:
                    raise AssertionError(
                        "aot_autograd() does not yet handle non-differentiable view input mutations."
                    )
        base_args.append(synthetic_base)
        base_args_descs.append(synthetic_base_desc)
        for curr_view_idx in aliased_input_indices:
            curr_view = fwd_inputs[curr_view_idx]
            base_idx = len(base_args) - 1
            # We store just enough info here so that we can regenerate the view later.
            # Regeneration: curr_view._view_func(args[base_idx])
            inner_calling_convention_meta[curr_view_idx] = (base_idx, curr_view)
    if len(base_args) == 0:
        if len(other_args) != len(fwd_inputs):
            raise AssertionError(
                f"expected len(other_args) == len(fwd_inputs), "
                f"got {len(other_args)} != {len(fwd_inputs)}"
            )
        # If no synthetic bases are necessary, just return the original inputs.
        return fwd_inputs, fwd_inputs_descs, None
    else:
        from torch.fx.experimental.symbolic_shapes import SymIntEqByExpr

        def make_hashable(arg: Any) -> Any:
            if isinstance(arg, torch.SymInt):
                # Since only nested SymInt objects can be hashed, we wrap them with
                # SymIntEqByExpr, which is a hashable wrapper of SymInts.
                return SymIntEqByExpr(arg)
            return arg

        # Otherwise, return:
        # (1) The new args according to the updated calling convention: (synthetic_bases, other_args)
        # (2) Metadata telling functionalization how to generate the inner argument list given the outer calling convention.
        #     We post-process it into a list, where meta[i] tells you info about the i'th argument in the inner calling convention.
        args_to_functionalization = base_args + other_args
        args_to_functionalization_descs = base_args_descs + other_args_descs

        # Map each argument into its old index.
        # There may be some repeated arguments, so we collect their indices in a list.
        arg_to_old_idx_map = collections.defaultdict(list)
        for i, arg in enumerate(fwd_inputs):
            arg_to_old_idx_map[make_hashable(arg)].append(i)
        # Reverse the list of each argument, so that we can easily pop them one-after-the-other in order.
        for hashable_arg in arg_to_old_idx_map:
            arg_to_old_idx_map[hashable_arg] = list(
                reversed(arg_to_old_idx_map[hashable_arg])
            )

        for i, other_arg in enumerate(other_args):
            new_idx = len(base_args) + i
            old_idx = arg_to_old_idx_map[make_hashable(other_arg)].pop()
            inner_calling_convention_meta[old_idx] = new_idx

        # post process into a list
        post_processed_calling_convention_meta: list[int | tuple[int, torch.Tensor]] = [
            -1 for _ in range(len(inner_calling_convention_meta))
        ]
        for k, v in inner_calling_convention_meta.items():
            post_processed_calling_convention_meta[k] = v
        # Quick assert: every argument in the inner calling convention should be accounted for.
        for x in post_processed_calling_convention_meta:
            if x == -1:
                raise AssertionError(
                    "every argument in the inner calling convention should be accounted for"
                )
        # pyrefly: ignore [bad-return]
        return (
            args_to_functionalization,
            args_to_functionalization_descs,
            post_processed_calling_convention_meta,
        )