def save_from_forward(self, ctx: Any, fw_outs: Sequence[Any]) -> None:
        tensors_saved_with_vc_check = fw_outs[
            self.metadata.tensors_saved_for_backwards_with_vc_check_slice
        ]
        tensors_saved_no_vc_check = fw_outs[
            self.metadata.tensors_saved_for_backwards_no_vc_check_slice
        ]
        if not all(isinstance(x, torch.Tensor) for x in tensors_saved_with_vc_check):
            raise AssertionError(
                "expected all tensors_saved_with_vc_check to be Tensors, "
                f"got types: {[type(x) for x in tensors_saved_with_vc_check]}"
            )
        if not all(isinstance(x, torch.Tensor) for x in tensors_saved_no_vc_check):
            raise AssertionError(
                "expected all tensors_saved_no_vc_check to be Tensors, "
                f"got types: {[type(x) for x in tensors_saved_no_vc_check]}"
            )

        # See Note [Detaching saved tensors in AOTAutograd]
        num_vc_check = len(tensors_saved_with_vc_check)
        tensors_to_save = [
            x.detach() if x._is_view() else x for x in tensors_saved_with_vc_check
        ]
        tensors_no_vc_check = [
            x.detach() if x._is_view() else x for x in tensors_saved_no_vc_check
        ]

        # dynamic_saved_tensors_idxs has indices relative to all saved tensors
        # (vc_check + no_vc_check combined). Mark dynamics on the detached tensors.
        for idx, dims in self.metadata.dynamic_saved_tensors_idxs.items():
            if idx < num_vc_check:
                maybe_mark_dynamic_helper(tensors_to_save[idx], dims)
            else:
                maybe_mark_dynamic_helper(tensors_no_vc_check[idx - num_vc_check], dims)

        ctx.save_for_backward(*tensors_to_save)
        ctx._tensors_no_vc_check = tensors_no_vc_check

        symint_outs = fw_outs[self.metadata.symints_saved_for_backwards_slice]
        if not all(
            isinstance(x, (int, float, torch.SymInt, torch.SymFloat))
            for x in symint_outs
        ):
            raise AssertionError(
                "expected all symint_outs to be int/float/SymInt/SymFloat, "
                f"got types: {[type(x) for x in symint_outs]}"
            )
        ctx.symints = symint_outs

        opaque_object_outs = fw_outs[
            self.metadata.opaque_objects_saved_for_backwards_slice
        ]
        if not all(
            is_opaque_type(type(obj)) or isinstance(obj, OpaqueBase)
            for obj in opaque_object_outs
        ):
            raise AssertionError(
                "expected all opaque_object_outs to be opaque types, "
                f"got types: {[type(obj) for obj in opaque_object_outs]}"
            )
        ctx.opaque_objects = opaque_object_outs