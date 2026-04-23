def should_compile_partial_graph(self) -> bool:
        if sys.version_info >= (3, 11):
            # Do not compile if current instruction's block is not the top with block
            entry = self.current_instruction.exn_tab_entry
            if entry and (
                not self.block_stack or entry.target is not self.block_stack[-1].target
            ):
                return False
        return (
            all(b.can_restore() for b in self.block_stack)
            and not self.one_graph
            # Only the leaf tracer's error_on_graph_break should be used
            and (self.is_child_tracer_active or not self.error_on_graph_break)
            and not self.is_tracing_resume_prologue
            and not self.active_generic_context_managers
            # Do not allow nested graph breaks in HOPs
            and self.output.current_tracer.parent is None
        )