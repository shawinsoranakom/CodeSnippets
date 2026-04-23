def has_metadata_mutation(
    f_arg: object, arg: object, *, check_only_storage_mutation: bool
) -> bool:
    if is_traceable_wrapper_subclass(f_arg):
        attrs, _ = f_arg.__tensor_flatten__()
        # A tensor subclass was updated if any of its inner elements were updated
        for attr in attrs:
            match getattr(f_arg, attr):
                case Tensor():
                    f_inner_t = getattr(f_arg, attr)
                    inner_t = getattr(arg, attr)
                    if has_metadata_mutation(
                        f_inner_t,
                        inner_t,
                        check_only_storage_mutation=check_only_storage_mutation,
                    ):
                        return True
                case OpaqueBase():
                    pass
                case unexpected:
                    raise AssertionError(
                        f"expected Tensor or OpaqueBase, got {type(unexpected)}"
                    )
        return False
    else:
        if not isinstance(f_arg, torch.Tensor):
            if isinstance(arg, torch.Tensor):
                raise AssertionError(
                    f"f_arg is not a Tensor but arg is: {type(f_arg)} vs {type(arg)}"
                )
            return False
        if not isinstance(f_arg, FunctionalTensor):
            raise AssertionError(
                f"expected FunctionalTensor for f_arg, got {type(f_arg)}"
            )
        if not isinstance(arg, FakeTensor):
            raise AssertionError(f"expected FakeTensor for arg, got {type(arg)}")

        arg_after = torch._from_functional_tensor(f_arg.elem)
        # This is true if the current tensor experienced at least one set_() call
        maybe_storage_changed = torch._functionalize_was_storage_changed(f_arg.elem)  # type: ignore[attr-defined]
        # However, multiple set_() calls can cancel out. So we also check whether the
        # storage of the tensor has changed.
        # Note: if an input experienced two set_() calls that cancel out, **and**
        # it experiences an data mutation, we pessimistically think that the set_()
        # call is necessary here. We could in theory fix this, but this will
        # hopefully never happen in user code, and is not needed for fsdp.
        if is_sparse_any(arg):
            # TODO:add sparse tensors support to functionalization
            same_storages = False
        else:
            same_storages = StorageWeakRef(arg.untyped_storage()) == StorageWeakRef(
                arg_after.untyped_storage()
            )
        has_storage_metadata_mutation = maybe_storage_changed and not same_storages
        if check_only_storage_mutation:
            return has_storage_metadata_mutation

        # storage metadata mutation is a type of metadata mutation, so return true if we saw one
        if has_storage_metadata_mutation:
            return True

        maybe_metadata_mutated = torch._functionalize_has_metadata_mutation(f_arg.elem)  # type: ignore[attr-defined]
        # This is true if the current tensor experienced at least one metadata mutation.
        # So if false, we know there was no metadata mutation
        if not maybe_metadata_mutated:
            return False

        # However, multi metadata mutations can cancel out.
        # So we also check if the concrete sizes/strides on the tensor have changed.
        same_sizes = arg.shape == arg_after.shape
        same_strides = arg.stride() == arg_after.stride()
        same_offsets = arg.storage_offset() == arg_after.storage_offset()
        has_metadata_mutation_ = maybe_metadata_mutated and not (
            same_sizes and same_strides and same_offsets
        )
        # We consider a tensor to have been metadata mutated if its storage was mutated through a set_() call.
        return has_metadata_mutation_