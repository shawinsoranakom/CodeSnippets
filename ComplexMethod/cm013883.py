def wrapper(self: InstructionTranslatorBase, inst: Instruction) -> None:
            prev_push = self.current_instruction_push
            self.current_instruction_push = push
            speculation = self.speculate()
            if speculation.failed(self):
                # no need to restore current_instruction_push if speculation failed
                assert speculation.reason is not None
                return handle_graph_break(self, inst, speculation.reason)
            try:
                return inner_fn(self, inst)
            except (Unsupported, UserError) as excp:
                if self.active_generic_context_managers:
                    # raise original graph break if fullgraph/error_on_graph_break=True
                    if self.one_graph or self.error_on_graph_break:
                        raise

                    # We don't support graph break under GenericContextWrappingVariable,
                    # If there is, we roll back to the checkpoint and fall back.
                    if isinstance(excp, Unsupported):
                        excp.remove_from_stats()
                    unimplemented(
                        gb_type="Graph break under GenericContextWrappingVariable",
                        context=f"Active generic context managers: {self.active_generic_context_managers}",
                        explanation="Attempted to graph break in an active context manager(s) that doesn't support graph breaking.",
                        hints=[
                            "Move the offending context manager(s) to outside the compiled region.",
                            *graph_break_hints.CAUSED_BY_EARLIER_GRAPH_BREAK,
                        ],
                        from_exc=excp,
                    )

                if getattr(excp, "skip_frame", False):
                    raise

                if not self.should_compile_partial_graph():
                    raise

                if self.maybe_has_backedge():
                    self.raise_loop_graph_break(self.f_code, excp)

                self.log_graph_break(
                    self.code_options,
                    reason=f"{msg_prefix}:\n\n{str(excp)}",
                    exc=excp,
                )

                if isinstance(excp, Unsupported):
                    excp.remove_from_stats()
                    excp.add_to_stats("graph_break")
                speculation.reason = GraphCompileReason(
                    getattr(excp, "msg", str(excp)),
                    getattr(excp, "real_stack", [self.frame_summary()]),
                )
            finally:
                self.current_instruction_push = prev_push
            speculation.fail_and_restart_analysis(self.error_on_graph_break)