def handle_graph_break(
            self: InstructionTranslatorBase,
            inst: Instruction,
            reason: GraphCompileReason,
        ) -> None:
            if (
                sys.version_info >= (3, 11)
                and sys.version_info < (3, 12)
                and inst.opname == "CALL"
            ):
                # stack effect for PRECALL + CALL is split between the two instructions
                stack_effect = dis.stack_effect(
                    dis.opmap["PRECALL"], inst.arg
                ) + dis.stack_effect(dis.opmap["CALL"], inst.arg)
            else:
                stack_effect = dis.stack_effect(inst.opcode, inst.arg)

            log.debug("%s triggered compile", inst.opname)
            all_stack_locals_metadata = self.output.compile_subgraph(
                self, reason=reason, stack_pops=int(push) - stack_effect
            )
            cg = PyCodegen(self.output.root_tx)
            cleanup: list[Instruction] = []
            _reconstruct_block_stack(self, cg, cleanup)
            self.output.add_output_instructions(cg.get_instructions())
            del cg

            if sys.version_info >= (3, 11) and inst.opname == "CALL":
                kw_names = (
                    self.kw_names.as_python_constant()
                    if self.kw_names is not None
                    else ()
                )
                if len(kw_names) > 0:
                    # KW_NAMES no longer used in 3.13
                    assert sys.version_info < (3, 13)
                    self.output.add_output_instructions(
                        [create_instruction("KW_NAMES", argval=kw_names)]
                    )
                assert inst.arg is not None
                call_insts = create_call_function(inst.arg, False)
                call_insts[-1].copy_positions(inst)
                self.output.add_output_instructions(call_insts)
            else:
                # copy instruction, but without exception table data
                assert inst.target is None
                inst_copy = copy.copy(inst)
                inst_copy.exn_tab_entry = None
                self.output.add_output_instructions([inst_copy])

            self.output.add_output_instructions(cleanup)

            self.popn(int(push) - stack_effect)
            if push:
                self.push(UnknownVariable())
            self.output.add_output_instructions(
                self.create_call_resume_at(
                    self.next_instruction,
                    all_stack_locals_metadata,
                )
            )