def handle_aliases_for_stolen_lists(
        self, tx: "InstructionTranslatorBase"
    ) -> tuple[list[Instruction], dict[Source, Source]]:
        # If list inputs are stolen, but still needed after the function call, create aliases to keep them alive
        maybe_gm = self.local_scope.get("self")
        stolen_list_names = get_locals_to_steal(maybe_gm)
        if not stolen_list_names:
            return [], {}

        alias_insts = []
        needs_alias: dict[str, list[VariableTracker]] = {}

        queue = [
            *tx.stack,
            *tx.symbolic_locals.values(),
            *self.side_effects.store_attr_mutations.keys(),
        ]

        while queue:
            x = queue.pop()
            if isinstance(x, BaseListVariable):
                assert isinstance(x.items, list)
                queue += x.items
                continue

            if not (
                (
                    x not in self.side_effects.store_attr_mutations
                    or isinstance(x.mutation_type, AttributeMutationExisting)
                )
                and isinstance(x.source, GetItemSource)
                and isinstance(x.source.base, LocalSource)
                and x.source.base.local_name in stolen_list_names
            ):
                continue

            stolen_name = x.source.base.local_name
            if stolen_name not in needs_alias:
                needs_alias[stolen_name] = []
            needs_alias[stolen_name].append(x)

        # pyrefly: ignore [implicit-any]
        visited = {}
        overridden_sources: dict[Source, Source] = {}
        for arg in self.graphargs:
            if not (
                isinstance(arg._example, list)
                and isinstance(arg.source, LocalSource)
                and arg.source.local_name in needs_alias
            ):
                continue

            # arg is a list that will be cleared by the compiled function
            list_name = arg.source.local_name
            assert list_name in self.code_options["co_varnames"]
            for x in needs_alias[list_name]:
                # Skip if already handled.
                if x.source in overridden_sources:
                    continue

                # A small codegen optimization because we might have different
                # VariableTrackers that share the same source.
                assert x.source is not None
                list_idx = x.source.index  # type: ignore[attr-defined]
                if list_idx not in visited:
                    alias_name = self.new_var(
                        f"{list_name}_ref"
                    )  # self.new_var already adds unique id suffix

                    visited[list_idx] = alias_name
                    # bytecode of `alias_name = list_name[list_idx]`
                    alias_insts.extend(
                        [
                            create_instruction("LOAD_FAST", argval=list_name),
                            create_load_const(list_idx),
                            create_binary_subscr(),
                            create_instruction("STORE_FAST", argval=alias_name),
                        ]
                    )

                # operate on alias, handled by suffix codegen
                assert x.source is not None
                old_source = x.source
                overridden_sources[old_source] = LocalSource(visited[list_idx])

        # NOTE: we need `overridden_sources` because (1) we want to codegen for
        # these list items to use the new local source, but (2) we want to avoid
        # updating `source` in place because that might break invariants in
        # other parts of Dynamo like guards.
        return alias_insts, overridden_sources