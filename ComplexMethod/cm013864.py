def exception_handler(self, raised_exception: ObservedException) -> None:
        observed_exn_gb_explanation = (
            "Dynamo found no exception handler at the top-level compiled function "
            "when encountering an exception. Exception will propagate outside the compiled region."
        )

        def bubble_exception_to_interpreter() -> None:
            # Bubble the exception to the interpreter
            curr_exc = self.exn_vt_stack.get_current_exception()
            dynamo_exc = exc.get_dynamo_observed_exception(curr_exc.python_type())
            assert isinstance(raised_exception, dynamo_exc)  # sanity check
            unimplemented(
                gb_type="Observed exception",
                context=f"raised exception {curr_exc.debug_repr()}",
                explanation=observed_exn_gb_explanation,
                hints=[
                    *graph_break_hints.USER_ERROR,
                    *graph_break_hints.SUPPORTABLE,
                ],
                from_exc=raised_exception,
            )

        if sys.version_info >= (3, 11):
            exn_tab_entry = self.current_instruction.exn_tab_entry
            if exn_tab_entry:
                # Implementation is based on https://github.com/python/cpython/blob/3.11/Objects/exception_handling_notes.txt

                # 1) pop values from the stack until it matches the stack depth
                # for the handler
                while len(self.stack) > exn_tab_entry.depth:
                    self.pop()

                # 2) if 'lasti' is true, then push the offset that the exception was raised at
                if exn_tab_entry.lasti:
                    self.push(
                        VariableTracker.build(self, self.current_instruction.offset)
                    )

                # 3) push the exception to the stack
                self.push(self.exn_vt_stack.get_current_exception())

                # 4) jump to the handler
                self.jump(exn_tab_entry)  # type: ignore[arg-type]
            else:
                # No handler found. Bubble the exception to the parent
                # instruction translator. We use special exception for this.
                self.stack.clear()

                # attach traceback to the exception and set it as current exception
                curr_exc = self.exn_vt_stack.get_current_exception()
                self._attach_traceback_to_exception(curr_exc)

                if type(self) is InstructionTranslator:
                    bubble_exception_to_interpreter()
                raise raised_exception
        else:
            if len(self.block_stack):
                # base implementation - https://github.com/python/cpython/blob/3.10/Python/ceval.c#L4455

                block_stack_entry = self.block_stack.pop()

                while block_stack_entry.inst.opname == "EXCEPT_HANDLER":
                    # TODO(anijain2305) - This is not tested .. unable to create a testcase
                    # https://github.com/python/cpython/blob/3.10/Python/ceval.c#L1456
                    self.popn(3)
                    self.exn_vt_stack.pop()
                    if len(self.block_stack) == 0:
                        # No handler found in this frame. Bubble the exception to the parent
                        # instruction translator.
                        self.stack.clear()
                        if type(self) is InstructionTranslator:
                            unimplemented(
                                gb_type="Observed exception (EXCEPT_HANDLER)",
                                context=str(raised_exception),
                                explanation=observed_exn_gb_explanation
                                + " This graph break is unexpected.",
                                hints=[*graph_break_hints.DYNAMO_BUG],
                                from_exc=raised_exception,
                            )

                        raise raised_exception
                    block_stack_entry = self.block_stack.pop()

                exception_var = self.exn_vt_stack.get_current_exception()
                self.exn_vt_stack.move_current_exception_to_stack()

                # 1) pop values from the stack until it matches the stack depth
                # for the handler
                while len(self.stack) > block_stack_entry.stack_index:
                    self.pop()

                # Push a dummy block stack entry of EXCEPT_HANDLER
                # https://github.com/python/cpython/blob/3.10/Python/ceval.c#L1456
                except_handler_inst = Instruction(int(1e6), "EXCEPT_HANDLER", None, 0)
                self.block_stack.append(
                    BlockStackEntry(except_handler_inst, None, len(self.stack))
                )

                # Push old exception
                if len(self.exn_vt_stack) >= 2:
                    old_exception = self.exn_vt_stack[-2]

                    # Push the old exception on to stack - tb, value, type
                    # Traceback is currently mapped to UnknownVariable
                    self.push(variables.UnknownVariable())
                    self.push(old_exception)

                    self.push(variables.BuiltinVariable(old_exception.exc_type))
                else:
                    # Push empty exception tb, value, type
                    self.push(ConstantVariable.create(None))
                    self.push(ConstantVariable.create(None))
                    self.push(ConstantVariable.create(None))

                # Push new exception - tb, val, type
                # Traceback is currently mapped to UnknownVariable
                self.push(variables.UnknownVariable())
                self.push(exception_var)

                self.push(variables.BuiltinVariable(exception_var.exc_type))

                # Jump to target
                self.jump(block_stack_entry)
            else:
                # No handler found. Bubble the exception to the parent
                # instruction translator. We use special exception for this.
                self.stack.clear()
                if type(self) is InstructionTranslator:
                    bubble_exception_to_interpreter()
                raise raised_exception