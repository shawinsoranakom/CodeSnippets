def _apply_input_mutations(
        self, orig_inputs: dict[int, Any], updated_inputs: list[Any]
    ) -> None:
        for i, inpt_idx in enumerate(self.runtime_metadata.mutated_inp_runtime_indices):
            meta = self.runtime_metadata.input_info[inpt_idx]
            if not meta.mutates_data and not meta.mutates_metadata:
                continue
            original_inpt = orig_inputs[inpt_idx]
            updated_inpt = updated_inputs[i]
            if meta.mutates_storage_metadata:
                # See Note [set_() Input Mutations in AOTAutograd]
                # mutates_storage_metadata means our input saw a x.set_(y) call.
                # What if x **also** saw a data and/or a metadata mutation?
                # (1) If the [meta]data mutation occurred after the set_(),
                #     then there is no need to copy_() the data.
                #     When we perform x.set_(x_updated), we are guaranteed that
                #     x_updated already has the final version of the data/metadata
                # (2) If a data mutation occurred before the set_().
                #     This case seems very difficult to support.
                #     TODO: discuss on the PR and decide if we want to tr to
                #     either support it, or detect and ban it.
                if self.trace_joint:
                    if not isinstance(updated_inpt, TensorAlias):
                        raise AssertionError(
                            f"expected TensorAlias for updated_inpt, got {type(updated_inpt)}"
                        )
                    updated_inpt = updated_inpt.alias
                with torch.no_grad():
                    original_inpt.set_(updated_inpt)
                continue
            if meta.mutates_metadata and not meta.mutates_data:
                if self.trace_joint:
                    if not isinstance(updated_inpt, TensorAlias):
                        raise AssertionError(
                            f"expected TensorAlias for updated_inpt, got {type(updated_inpt)}"
                        )
                    updated_inpt = updated_inpt.alias
                # We need to grab the size/stride/storage_offset from the compiled forward,
                # and use that to mutate the metadata of the input
                original_inpt.as_strided_(
                    updated_inpt.size(),
                    updated_inpt.stride(),
                    updated_inpt.storage_offset(),
                )
            else:
                if meta.mutates_data and meta.mutates_metadata:
                    original_inpt.as_strided_(
                        updated_inpt.size(),
                        updated_inpt.stride(),
                        updated_inpt.storage_offset(),
                    )
                else:
                    if not meta.mutates_data:
                        raise AssertionError("expected meta.mutates_data to be True")
                if meta.is_leaf and original_inpt.requires_grad:
                    # We can hit this situation in this case:
                    #   def f(x):
                    #       x.detach().mul_(2)
                    #       return x + 1
                    # AOTAutograd will see a mutation in the above case, and try to
                    # apply a copy_() here, in the epilogue.
                    # But if x required gradients, and is a leaf, then autograd
                    # will yell at us for trying to mutate it.
                    # However, it's only possible to end up in this scenario (like the above)
                    # if all of the mutations to the leaf input were non-autograd-tracking mutations
                    # (aka mutations under no_grad(), or on detached views).
                    # In that case, we fully want to hide the mutation from autograd, so detaching is ok.
                    original_inpt.detach().copy_(updated_inpt)
                else:
                    # Check if we have stream index information for this mutated input
                    if (
                        self.runtime_metadata.mutated_inp_stream_indices is not None
                        and i < len(self.runtime_metadata.mutated_inp_stream_indices)
                        and self.runtime_metadata.mutated_inp_stream_indices[i]
                        is not None
                    ):
                        raise RuntimeError(
                            "Mutations on inputs with user-specified streams are not yet supported. "
                            "See: https://github.com/pytorch/pytorch/issues/172522"
                        )
                    original_inpt.copy_(updated_inpt)