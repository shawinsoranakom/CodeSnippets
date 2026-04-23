def enter_ctx(
        self,
        ctx: ContextWrappingVariable | GenericContextWrappingVariable,
        inst: Instruction,
    ) -> VariableTracker:
        if (
            isinstance(ctx, GenericContextWrappingVariable)
            and not ctx.supports_graph_breaks()
        ):
            self.active_generic_context_managers.append(ctx)

        if sys.version_info >= (3, 11):
            # See update_block_stack/create_resume for block stack details.
            # Only push a block if the current instruction's block is a
            # with block that is not nested in a try block - that is, the current
            # instruction's block target is the same as the top block's target.
            if inst.exn_tab_entry and (
                not self.block_stack
                or inst.exn_tab_entry.target is not self.block_stack[-1].target
            ):
                target = None
            else:
                assert self.next_instruction.exn_tab_entry is not None
                target = self.next_instruction.exn_tab_entry.target
        else:
            target = inst.target

        if target:
            if isinstance(self, InstructionTranslator) or config.nested_graph_breaks:
                self.block_stack.append(
                    BlockStackEntry(inst, target, len(self.stack), ctx)
                )
            else:
                self.block_stack.append(BlockStackEntry(inst, target, len(self.stack)))

        return ctx.enter(self)