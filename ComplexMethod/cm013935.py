def build_guards(
        self,
        sorted_guards: list[Guard],
        existing_diff_guard_sources: OrderedSet[str],
        f_code: types.CodeType,
        output_graph: OutputGraphGuardsState,
        save_guards: bool,
        guard_filter_fn: Callable[[Sequence[GuardFilterEntry]], Sequence[bool]]
        | None = None,
    ) -> tuple[GuardBuilder, GuardManagerWrapper]:
        guard_manager = GuardManagerWrapper()
        guard_manager.diff_guard_sources = existing_diff_guard_sources

        w_builder = None

        def source_ref(source: Source) -> str:
            guard_source = source.guard_source
            if guard_source is GuardSource.CONSTANT:
                # No need to track constants
                return source.name
            assert w_builder
            r_builder = w_builder()
            assert r_builder is not None
            return r_builder.arg_ref(source.name)

        builder = GuardBuilder(
            f_code,
            self.id_ref,
            source_ref,
            self.lookup_weakrefs,
            output_graph.local_scope,
            output_graph.global_scope,
            guard_manager,
            self,
            save_guards,
            runtime_global_scope=self.runtime_global_scope,
            guard_filter_fn=guard_filter_fn,
        )

        # Break retain cycle. See test_release_scope_memory
        def cleanup_builder(weak_b: weakref.ref[GuardBuilder]) -> None:
            b = weak_b()
            if b:
                b.scope = None  # type: ignore[assignment]

        # Break retain cycle. See test_release_input_memory
        w_builder = weakref.ref(builder, cleanup_builder)

        guard_on_nn_modules = config.guard_nn_modules and justknobs_check(
            "pytorch/compiler:guard_nn_modules"
        )

        for guard in sorted_guards:
            if (
                not guard_on_nn_modules
                and guard.is_specialized_nn_module()
                # Default func args must be guarded on.
                # TODO: we could make use of 'DefaultsSource' and offer a .guard.is_defaults() API
                and "__defaults__" not in guard.name
                and "__kwdefaults__" not in guard.name
                and (config.skip_nnmodule_hook_guards or "hooks" not in guard.name)
            ):
                continue

            guard.create(builder)
        return builder, guard_manager