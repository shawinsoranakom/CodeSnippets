def make_runtime_safe(self) -> None:
        """
        There are various fields in ViewAndMutationMeta that aren't serializable. This function is called after all tracing
        is completed to simplify certain fields in the metadata so that they can be safely cached.

        Doing so may lose information (in the case of traced_tangents), but none of the information is needed at runtime.
        """
        # TODO: This function is only a best effort: there are other fields that may not be cache safe
        # (i.e., there's no guarantee that tensor_flatten() returns a serializable result), or that
        # SubclassCreationMeta is cache safe.
        if self.traced_tangent_metas is not None:
            raise AssertionError(
                "traced_tangent_metas should be None before calling make_runtime_safe"
            )

        def extract_metadata(t: object) -> tuple[Sequence[str], object] | None:
            if isinstance(t, torch.Tensor) and is_traceable_wrapper_subclass(t):
                (inner_tensors, flatten_spec) = t.__tensor_flatten__()  # type: ignore[attr-defined]
                # Technically, we only need the flatten_spec, not the inner tensors.
                # However, some Tensor subclasses (like TwoTensor) may have flatten_spec = None.
                # And we want to be able to assert that this metadata is non-None,
                # to distinguish between "this was a tensor subclass with no metadata" vs.
                # "this wasn't a tensor subclass at all".
                return (inner_tensors, flatten_spec)
            else:
                return None

        self.traced_tangent_metas = [extract_metadata(t) for t in self.traced_tangents]
        # Clear traced tangents at runtime
        self.traced_tangents = []
        for inp_meta in self.subclass_inp_meta:
            if isinstance(inp_meta, SubclassCreationMeta):
                inp_meta.make_runtime_safe()
        for inp_meta in self.subclass_fw_graph_out_meta:
            if isinstance(inp_meta, SubclassCreationMeta):
                inp_meta.make_runtime_safe()
        for inp_meta in self.subclass_tangent_meta:
            if isinstance(inp_meta, SubclassCreationMeta):
                inp_meta.make_runtime_safe()

        # Clear view_meta_sequence when it has symbolic inputs, since it won't
        # be used at runtime anyway (gen_alias_from_base skips view replay for
        # symbolic inputs) and the SymInt references make it unpicklable.
        for i, out_info in enumerate(self.output_info):
            if out_info.view_meta_sequence is not None and any(
                vm.has_symbolic_inputs for vm in out_info.view_meta_sequence.sequence
            ):
                self.output_info[i] = replace(out_info, view_meta_sequence=None)