def run(self) -> None:
        with self.run_ctx_mgr():
            dump_file(self.f_code.co_filename)
            try:
                self.output.push_tx(self)
                self.start_point = self.instruction_pointer
                try:
                    while self.step():
                        pass
                except Exception as e:
                    if self.is_tracing_resume_prologue:
                        raise ResumePrologueTracingError(
                            "Error while tracing through a Dynamo-generated resume function prologue. "
                            "Errors are not allowed when tracing resume function prologues.\n"
                            f"{type(e).__qualname__}: {str(e)}"
                        ).with_traceback(e.__traceback__) from None
                    raise
            except TensorifyScalarRestartAnalysis:
                raise
            except BackendCompilerFailed:
                raise
            except RuntimeError as e:
                # If the root tx fails to handle the graph break, then the caller (convert_frame)
                # will skip the frame and fall back to eager.
                # This code path happens e.g. for bytecodes we don't support
                # or when we are unable to resume from a graph break.
                if (
                    isinstance(e, (Unsupported, UserError))
                    and isinstance(self, InstructionTranslator)
                    and not self.error_on_graph_break
                    and not self.one_graph
                ):
                    # log graph break if we won't error
                    reason = (
                        "Failed to handle graph break gracefully. "
                        "Skipping the function and falling back to eager. "
                        f"Graph break encountered:\n\n{str(e)}"
                    )
                    self.log_graph_break(
                        self.code_options,
                        reason=reason,
                        exc=e,
                    )

                if not isinstance(e, exc.RestartAnalysis):
                    self.output.side_effects.log_side_effects_summary()

                if hasattr(e, "msg") and "Data-dependent" in e.msg:
                    readable_graph = torch.fx.GraphModule(
                        self.output.nn_modules, self.output.graph
                    ).print_readable(
                        print_output=False, include_stride=True, include_device=True
                    )
                    e.partial_fx_graph = readable_graph  # type: ignore[attr-defined]
                    raise

                raise
            except Exception as e:
                if self.exec_recorder:
                    e.exec_record = self.exec_recorder.get_record()  # type: ignore[attr-defined]
                if not isinstance(e, exc.RestartAnalysis):
                    self.output.side_effects.log_side_effects_summary()

                raise
            finally:
                self.output.pop_tx()
                # Cleanup the outputGraph to delete the held tensors. We perform the
                # cleanup only for InstructionTranslator and not
                # InliningInstructionTranslator. The InliningInstructionTranslator
                # mutates the output object and is restored to original state if
                # there was an exception.
                if isinstance(self, InstructionTranslator):
                    self.output.cleanup()

                    # Note that this call maybe redundant if compile_subgraph is
                    # called. This is ok, because calling exit stack close()
                    # twice is not an issue (second stop is a no op).
                    self.output.mark_bytecode_tracing_stop()