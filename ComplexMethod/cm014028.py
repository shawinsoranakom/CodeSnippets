def add_fqn_info_for_inlined_modules(
        self, inlined_module: torch.nn.Module, source: Source
    ) -> None:
        name = OutputGraph.module_key_name(source.name)
        name = get_unique_name_wrt(
            name, self.used_inlined_inbuilt_modules_names, self.global_scope
        )
        self.used_inlined_inbuilt_modules_names.add(name)

        def register_leaf_name(leaf_name: str) -> None:
            assert self.param_name_to_source is not None
            new_source = self.get_chained_param_buffer_source(source, leaf_name)
            new_name = f"{name}.{leaf_name}"
            self.param_name_to_source[new_name] = new_source
            if isinstance(source, LocalSource):
                self.dynamo_flat_name_to_original_fqn[
                    OutputGraph.module_key_name(new_source.name)
                ] = leaf_name

        # annoying, but there are cases when we do not have parameters
        # see test_nn_moduledict_contains
        if hasattr(inlined_module, "_parameters"):
            if (
                callable(inlined_module.named_parameters)
                and inlined_module.named_parameters.__func__  # type: ignore[attr-defined]
                is og_module_named_parameters_fn_ptr
            ):
                for leaf_name, _ in inlined_module.named_parameters():
                    register_leaf_name(leaf_name)
        if hasattr(inlined_module, "_buffers"):
            if (
                callable(inlined_module.named_buffers)
                and inlined_module.named_buffers.__func__  # type: ignore[attr-defined]
                is og_module_named_buffers_fn_ptr
            ):
                for leaf_name, _ in inlined_module.named_buffers():
                    register_leaf_name(leaf_name)