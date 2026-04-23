def inline_call_(self) -> VariableTracker:
        parent = self.parent
        parent.has_no_inlined_calls = False
        parent.is_child_tracer_active = True
        code = self.f_code

        strict_ctx: Any = contextlib.nullcontext()
        if parent.strict_checks_fn:
            strict_ctx = self.strict_translation_mode(parent.strict_checks_fn)

        try:
            with strict_ctx:
                self.run()
        except exc.ObservedException as e:
            msg = f"Observed exception DURING INLING {code} : {e}"
            log.debug(msg)
            # bubble up the exception to the parent frame.
            raise
        except (Unsupported, UserError) as e:
            # If this graph break has skip_frame set, unset it
            # since it refers to the current frame and not the parent.
            e.skip_frame = False
            raise
        except Exception:
            log.debug("FAILED INLINING %s", code)
            raise
        finally:
            # Pass inlined tx's error_on_graph_break to parent.
            # Deals with the case where the parent's error_on_graph_break is True
            # while the inlined tx's error_on_graph_break was set to False.
            parent.error_on_graph_break = self.error_on_graph_break
            parent.is_child_tracer_active = False

        if self.output.should_exit:
            # graph break
            return ConstantVariable.create(None)  # return dummy variable

        assert self.symbolic_result is not None

        if self.f_globals is parent.f_globals:
            # Merge symbolic_globals back if parent and child are in the same namespace
            parent.symbolic_globals.update(self.symbolic_globals)

        parent.inconsistent_side_effects |= self.inconsistent_side_effects

        log.debug("DONE INLINING %s", code)
        self.output.tracing_context.traced_code.append(code)

        if config.enable_faithful_generator_behavior or (
            isinstance(self, InliningGeneratorInstructionTranslator)
            and self.is_generator_from_ctx_manager
        ):
            if (
                is_generator(code)
                and isinstance(self, InliningGeneratorInstructionTranslator)
                and self.generator_exhausted
            ):
                assert isinstance(self, InliningGeneratorInstructionTranslator)
                # When the generator returns None, we raise StopIteration
                # pyrefly: ignore [implicit-any]
                args = []
                if not self.symbolic_result.is_constant_none():
                    args = [self.symbolic_result]
                exc.raise_observed_exception(StopIteration, self, args=args)
            else:
                return self.symbolic_result
        else:
            if is_generator(code):
                assert isinstance(self, InliningGeneratorInstructionTranslator)
                assert self.symbolic_result.is_constant_none()
                return ListIteratorVariable(
                    self.generated_items,
                    mutation_type=ValueMutationNew(),
                )
            else:
                return self.symbolic_result