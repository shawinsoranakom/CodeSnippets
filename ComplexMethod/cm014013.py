def get_replayed_side_effect_source_refs(
        self, *, populate_export_metadata: bool = False
    ) -> list[str]:
        """Return Python-side effect sources that Dynamo replays outside the FX graph."""
        if (
            not populate_export_metadata
            and not self.side_effects.id_to_variable
            and self._cached_replayed_side_effect_source_refs is not None
        ):
            return list(self._cached_replayed_side_effect_source_refs)

        from torch.export._trace import _ExportModuleSpecTrackerDict

        potential_side_effects = []
        for var in self.side_effects._get_modified_vars():
            if hasattr(var, "mutation_type"):
                mut_type = var.mutation_type
                # Skip codegen-specific mutations that never materialize as
                # externally visible Python side effects.
                if isinstance(
                    mut_type, (AttributeMutationExisting, ValueMutationExisting)
                ):
                    if isinstance(var, UserDefinedDictVariable) and isinstance(
                        var.value, _ExportModuleSpecTrackerDict
                    ):
                        if populate_export_metadata:
                            assert var._base_vt is not None
                            for (
                                k,
                                v,
                            ) in (
                                var._base_vt.items.items()  # pyrefly: ignore[missing-attribute]
                            ):
                                # pyrefly: ignore [implicit-any]
                                specs = {}
                                # pyrefly: ignore[missing-attribute]
                                for k_spec, val in v.items.items():
                                    specs[k_spec.vt.as_python_constant()] = (
                                        val.as_python_constant()
                                    )
                                assert ["in_spec", "out_spec"] == list(specs.keys())
                                self.export_metadata.module_call_spec[
                                    # pyrefly: ignore[missing-attribute]
                                    k.vt.as_python_constant()
                                ] = specs
                    # export uses tracepoint pass to dump submodule inp/out spec
                    # into global state, so we filter it here
                    if not (
                        isinstance(var, UserDefinedDictVariable)
                        and isinstance(var.value, _ExportModuleSpecTrackerDict)
                    ):
                        potential_side_effects.append(var)

        return [_get_source_debug_name(var.source) for var in potential_side_effects]