def jump_graph_break(
        self: InstructionTranslatorBase,
        inst: Instruction,
        value: VariableTracker,
        extra_msg: str = "",
    ) -> None:
        assert self.should_compile_partial_graph()

        exc = None
        try:
            raise_jump_graph_break(value)
        except (Unsupported, UserError) as e:
            exc = e

        assert exc is not None

        # compile a partial subgraph prefix then skip the rest of user code
        if self.maybe_has_backedge():
            self.raise_loop_graph_break(self.f_code, exc)

        self.log_graph_break(
            self.code_options,
            reason=str(exc),
            exc=exc,
        )

        self.push(value)
        log.debug("generic_jump triggered compile")
        all_stack_locals_metadata = self.output.compile_subgraph(
            self,
            reason=GraphCompileReason(
                f"generic_jump {typestr(value)}{extra_msg}", [self.frame_summary()]
            ),
            stack_pops=1,
        )
        self.pop()

        if_next = self.create_call_resume_at(
            self.next_instruction,
            all_stack_locals_metadata,
        )
        if push:
            self.push(value)
        assert inst.target is not None
        if_jump = self.create_call_resume_at(
            inst.target,
            all_stack_locals_metadata,
        )

        if sys.version_info >= (3, 13):
            # 3.13 requires stack[-1] to be bool type
            self.output.add_output_instructions([create_instruction("TO_BOOL")])

        jump_inst = create_instruction(inst.opname, target=if_jump[0])
        jump_inst.copy_positions(inst)
        self.output.add_output_instructions([jump_inst] + if_next + if_jump)