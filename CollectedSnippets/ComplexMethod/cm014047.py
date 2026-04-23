def prune_dead_object_new(self, tx: "InstructionTranslatorBase") -> None:
        # Avoid VT cycles from e.g., recursive function.
        visited: set[VariableTracker] = set()
        live_new_objects: set[VariableTracker] = set()

        def visit(var: VariableTracker) -> None:
            if var in visited:
                return
            visited.add(var)
            # Object may have been mutated, store this mutation.
            if isinstance(var.mutation_type, AttributeMutationNew):
                live_new_objects.add(var)
            # It's possible that we have mutated the value of this variable
            # to be another one. The new value is in store_attr_mutations.
            # Also recurse through the new value to detect alive AttributeMutationNew.
            if var in self.store_attr_mutations:
                VariableTracker.visit(
                    visit,  # noqa: F821
                    self.store_attr_mutations[var],
                )

        def is_live(var: VariableTracker) -> bool:
            if isinstance(var.mutation_type, AttributeMutationNew):
                return var in live_new_objects
            return True

        pre_existing_vars = [
            var
            for var in self.id_to_variable.values()
            if not isinstance(var.mutation_type, AttributeMutationNew)
        ]

        # The only live side effects come from returns (tx.stack), any intermediates
        # during a graph break (tx.symbolic_locals), and mutation on pre-existing variables.
        # Recursively visit Variables and see if any of them have been mutated.
        init_live_vars = []
        # gather stack/symbolic_locals for all tx's up the chain
        cur_tx: InstructionTranslatorBase | None = tx
        while cur_tx is not None:
            init_live_vars.extend([cur_tx.stack, cur_tx.symbolic_locals])
            if cur_tx.parent is not None:
                # for non-root tx'es, also keep the cells/freevars alive so they get codegen'd properly
                # TODO see if we could prune dead cells - cell pruning information needs to be forwarded
                # to the resume function creation as well.
                assert cur_tx.post_prune_cell_and_freevars is not None
                init_live_vars.append(cur_tx.post_prune_cell_and_freevars)
            cur_tx = cur_tx.parent
        VariableTracker.visit(
            visit,
            # TODO track from all possible sources.
            init_live_vars
            + [
                pre_existing_vars,
                tx.output.backward_state,
                self.tensor_hooks,
            ],
        )
        # Manually release the self-referential function, which indirectly
        # captures certain `VariableTracker` and affects parts of PT test/logic
        # that are sensitive to when certain objects get released.
        del visit

        # NB: cell variable handling.is tricky.
        # cell variables must stay alive if any NestedUserFunctionVariable
        # are live. "visit"-ing the NestedUserFunctionVariable visits
        # the .closures field, from which we will see if we need to keep
        # any mutations to cell variables alive.

        self.id_to_variable = {
            k: v for k, v in self.id_to_variable.items() if is_live(v)
        }
        self.store_attr_mutations = {
            k: v for k, v in self.store_attr_mutations.items() if is_live(k)
        }