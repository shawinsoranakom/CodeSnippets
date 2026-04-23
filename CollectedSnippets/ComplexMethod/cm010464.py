def __new__(cls, elem: torch.Tensor, mode: FunctionalTensorMode) -> Self:
        if not torch._is_functional_tensor(elem):
            raise AssertionError("elem must be a functional tensor")

        # In general, we'd like our functional tensor subclass to only be in charge of functionalization,
        # and defer to the inner subclass for all other functionality.
        # Example: If our inner tensor is a ZeroTensor, we would want to defer running the ZeroTensor fallback
        # until after we redispatch to our inner ZeroTensor.
        # However, there are a few keys that we need to mirror between the inner and outer tensors.
        #   Conjugate
        #   Negative
        # Why? These keys are used to test metadata queries, like `.is_conj()` and `.is_neg()`.
        # We **need** calls to is_conj() to return the same thing on the outer and inner tensors,
        # Because user code / framework code that branches like so needs to do the same thing
        # when it sees the outer FunctionalTensor:
        #     if (x.is_conj()) {
        #         return at::view_as_real(x.resolve_conj());
        #     } else {
        #         return at::view_as_real(x);
        #     }
        extra_dispatch_keys = (
            FunctionalTensor._extra_dispatch_keys & torch._C._dispatch_keys(elem)
        )

        out = torch.Tensor._make_wrapper_subclass(
            # TODO: right now, _make_wrapper_subclass's dynamic shape interaction is not great.
            # Calling the overload that has kwargs causes us to go down the first overload path,
            # which will **always** specialize sizes.
            # We should probably eventually fix this so that the first overload can just handle dynamic shapes.
            cls,
            elem.shape,  # sizes
            elem.stride() if not is_sparse_any(elem) else None,  # strides
            (
                elem.storage_offset() if not is_sparse_any(elem) else None
            ),  # storage_offset
            None,  # memory_format
            elem.dtype,  # dtype
            elem.layout,  # layout
            elem.device,  # device
            False,  # pin_memory
            elem.requires_grad,  # requires_grad
            None,  # dispatch_sizes_strides_policy
            False,  # dispatch_device
            False,  # dispatch_layout
            extra_dispatch_keys,  # _extra_dispatch_keys
        )
        torch._C._set_throw_on_mutable_data_ptr(out)
        out.elem = elem

        if (
            torch._export.config.enable_auto_functionalized_v2_for_export
            and torch.is_inference_mode_enabled()
            and torch._inductor.config.enable_auto_functionalized_v2
        ):
            if out.is_base_tensor():
                out._inference_mode_base = None
                # This assumes that the FunctionalTensor.elem does not change its storage after this point.
                # Otherwise this would be invalid.
                mode._storage_to_base[out.elem.untyped_storage()] = out
            else:
                out._inference_mode_base = mode._storage_to_base[
                    out.elem.untyped_storage()
                ]
                if out._inference_mode_base is None:
                    raise AssertionError("out._inference_mode_base must not be None")
        return out