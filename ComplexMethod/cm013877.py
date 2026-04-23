def _return(self, inst: Instruction) -> None:
        self.replace_tos_if_return_is_generator()
        assert self.instruction_pointer is not None
        assert self.start_point is not None
        get_metrics_context().increment(
            "ir_count", self.instruction_pointer - self.start_point
        )

        if (
            not config.allow_empty_graphs
            and self.output.count_calls() == 0
            and not self.inconsistent_side_effects
            and not self.symbolic_locals_contain_module_class()
            and not self.export
            and not self.one_graph
            and not self.error_on_graph_break
            and not self.is_tracing_resume_prologue
        ):
            raise exc.SkipFrame(
                "No ops traced for the FX graph. `torch.compile` will skip the frame and fall back to eager.\n"
                f"Frame info: {format_frame_info(self.f_code)}"
            )

        self.instruction_pointer = None
        _step_logger()(
            logging.INFO,
            f"torchdynamo done tracing {self.f_code.co_name} ({inst.opname})",
        )
        log.debug("return triggered compile")
        all_stack_locals_metadata = self.output.compile_subgraph(
            self,
            reason=GraphCompileReason(
                "return_value", [self.frame_summary()], graph_break=False
            ),
            # the value to be returned
            stack_pops=1 if inst.opname == "RETURN_VALUE" else 0,
        )
        # check that our stack/locals meta are correct:
        # we should only be tracing 1 frame, and there should not be any NULLs on the stack
        assert len(all_stack_locals_metadata) == 1
        assert not all_stack_locals_metadata[0].stack_null_idxes
        self.output.add_output_instructions(
            self.codegen_return_with_pops(inst, all_stack_locals_metadata[0].num_stack)
        )
        raise ReturnValueOp