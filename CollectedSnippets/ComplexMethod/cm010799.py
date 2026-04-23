def creation_fn(
        self,
        all_args: Sequence[torch.Tensor | IntLikeType | OpaqueBase],
        *,
        is_runtime: bool,
    ) -> torch.Tensor:
        inner_tensors: dict[str, torch.Tensor | OpaqueBase] = {}

        curr_start_idx = self.flat_tensor_start_idx
        for attr, creation_meta in self.attrs.items():
            if isinstance(creation_meta, OpaqueMeta):
                opaque = all_args[curr_start_idx]
                if not isinstance(opaque, OpaqueBase):
                    raise AssertionError(f"OpaqueBase expected, got {type(opaque)}")
                inner_tensors[attr] = opaque
                curr_start_idx += 1
                continue
            if isinstance(creation_meta, PlainTensorMeta):
                subclass = all_args[curr_start_idx]
                if not isinstance(subclass, Tensor):
                    raise AssertionError("Tensor expected")
                curr_start_idx += 1
            else:
                subclass = creation_meta.creation_fn(
                    all_args,
                    is_runtime=is_runtime,
                )
                curr_start_idx += creation_meta.arg_count
            inner_tensors[attr] = subclass

        if is_runtime:
            if self.original_subclass_type is None:
                raise AssertionError(
                    "original_subclass_type must not be None at runtime"
                )
            original_subclass_type = self.original_subclass_type
        else:
            original_subclass_type = type(self.original_subclass)

        if is_runtime:
            outer_size, outer_stride = self.compute_outer_size_and_stride(
                all_args,
                curr_start_idx=curr_start_idx,
            )
        else:
            outer_size, outer_stride = self.outer_size, self.outer_stride

        rebuilt = original_subclass_type.__tensor_unflatten__(  # type: ignore[attr-defined]
            inner_tensors, self.meta, outer_size, outer_stride
        )

        if not is_runtime:
            # After wrapping up the inner dense tensors into a subclass, we need to make sure that our new wrapper
            # has correct autograd metadata, since we'll be tracing through the autograd engine with the subclass.
            # We don't trace through the autograd engine at runtime though, so no need
            # to compute this extra metadata then!
            torch._mirror_autograd_meta_to(self.original_subclass, rebuilt)  # type: ignore[attr-defined]

        return rebuilt