def codegen_suffix(
        self,
        tx: "InstructionTranslatorBase",
        stack_values: list[VariableTracker],
        cg: PyCodegen,
        log_side_effects: bool,
    ) -> None:
        # NOTE: `codegen_save_tempvars` must run first to update `source` fields
        # for variables with `AttributeMutationNew`, as they don't implement
        # `reconstruct` themselves.
        self.side_effects.codegen_save_tempvars(cg)
        if self.backward_state:
            assert not self.export
            for name, val in self.backward_state.items():
                cg(val)
                assert self.backward_state_var is not None
                cg.append_output(cg.create_load(self.backward_state_var))
                cg.store_attr(name)
        if config.replay_side_effects:
            self.side_effects.codegen_hooks(cg)

        # TODO get debug_locals working for nested graph breaks
        # Return variables used for logging at the end
        for debug_var, args in tx.debug_locals:
            cg.add_push_null(lambda: cg(debug_var))
            for arg in args:
                cg(arg)
            cg.extend_output(create_call_function(len(args), False))
            cg.extend_output([create_instruction("POP_TOP")])

        # codegen cells before we apply side effects
        self.codegen_cells(tx, cg)

        cg.restore_stack(stack_values, value_from_source=not tx.export)
        self.side_effects.codegen_update_mutated(cg, log_side_effects)