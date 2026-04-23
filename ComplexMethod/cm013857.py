def inner(self: InstructionTranslatorBase, inst: Instruction) -> None:
        value: VariableTracker = self.pop()
        if (
            config.rewrite_assert_with_torch_assert
            and sys.flags.optimize == 0
            and _detect_and_normalize_assert_statement(self, truth_fn, push)
        ):
            error_msg: VariableTracker = self.pop()
            # Skip over things like `assert True`
            if value.is_python_constant():
                if bool(value.as_python_constant()):
                    return self.jump(inst)
                elif self.should_compile_partial_graph():
                    jump_graph_break(self, inst, value)
                    return
                else:
                    unimplemented(
                        gb_type="Data-dependent assertion failed (cannot compile partial graph)",
                        context=f"value: {value}",
                        explanation="Dynamo has determined when encountering a data-dependent assert failure "
                        "that it should not compile the partial graph.",
                        hints=[
                            *graph_break_hints.FUNDAMENTAL,
                            "Use `torch._assert()` to raise a hard AssertionError when the check fails. "
                            "This error will propagate back the user code "
                            "that called the compiled function (i.e. Dynamo will not trace any exception handling).",
                            "Remove the assert statement.",
                            "Move the assert statement outside of any context managers in order to graph break with "
                            "partial graph compilation (if fullgraph=False).",
                        ],
                    )

            # TODO maybe should respect DtoH sync intention of users later??
            # Manually insert torch._assert_async instead of python assert and jump over
            # assert related instructions as we don't need them anymore.

            # if we see Tensor as assert statement, no need to call scalar_tensor
            if value.is_tensor():
                self.output.create_proxy(
                    "call_function",
                    torch._assert_async,
                    *proxy_args_kwargs((value, error_msg), {}),
                )
                self.jump(inst)
                return

            if isinstance(value, SymNodeVariable):
                # if the assertion is normal shape expression.
                # just install guard and bail out.
                sym_expr = value.sym_num
                if not isinstance(sym_expr, torch.SymBool):
                    sym_expr = sym_expr != 0

                result = torch.fx.experimental.symbolic_shapes.expect_true(sym_expr)
                if not result:
                    unimplemented(
                        gb_type="Assertion failed on symbolic shapes",
                        context=str(sym_expr),
                        explanation="",
                        hints=[*graph_break_hints.USER_ERROR],
                    )
                self.jump(inst)
                return

            scalar_to_tensor_proxy = self.output.create_proxy(
                "call_function", torch.scalar_tensor, *proxy_args_kwargs((value,), {})
            )

            scalar_to_tensor = wrap_fx_proxy(
                self,
                scalar_to_tensor_proxy,
                example_value=get_fake_value(scalar_to_tensor_proxy.node, self),
            )

            self.output.create_proxy(
                "call_function",
                torch._assert_async,
                *proxy_args_kwargs((scalar_to_tensor, error_msg), {}),
            )
            self.jump(inst)
            return

        if value.is_python_constant():
            # ConstDictVariable is optimized to be very lazy about insertion of
            # guards, so we have to manually insert a SEQUENCE_LENGTH guard
            # here.
            if isinstance(value, ConstDictVariable) and value.source:
                install_guard(value.source.make_guard(GuardBuilder.SEQUENCE_LENGTH))
            if truth_fn(value.as_python_constant()):
                if push:
                    self.push(value)
                self.jump(inst)
        elif value.is_tensor() and self.should_compile_partial_graph():
            jump_graph_break(self, inst, value)
        elif isinstance(value, NNModuleVariable):
            # Equivalent of "self.nn_module is not None"
            mod = self.output.get_submodule(value.module_key)
            if truth_fn(mod):
                if push:
                    self.push(value)
                self.jump(inst)
        elif isinstance(value, UserDefinedObjectVariable):
            try:
                x = value.var_getattr(self, "__bool__")  # type: ignore[arg-type]
            except exc.ObservedAttributeError:
                exc.handle_observed_exception(self)
                # if __bool__ is missing, trying __len__ to infer a truth value.
                try:
                    x = value.var_getattr(self, "__len__")  # type: ignore[arg-type]
                except exc.ObservedAttributeError:
                    exc.handle_observed_exception(self)
                    x = None

            # __bool__ or __len__ is function
            if isinstance(x, (GetAttrVariable, UserMethodVariable)):
                result = x.call_function(self, [], {})  # type: ignore[arg-type, assignment]
                method_name = getattr(getattr(x, "fn", None), "__name__", None)
                if result.is_python_constant():
                    result_value = result.as_python_constant()
                    if method_name == "__bool__" and not isinstance(result_value, bool):
                        exc.raise_observed_exception(
                            TypeError,
                            self,
                            args=[
                                f"__bool__ should return bool, returned {type(result_value).__name__}"
                            ],
                        )
                    if isinstance(result_value, (bool, int)) and truth_fn(result_value):
                        if push:
                            self.push(value)
                        self.jump(inst)
                elif isinstance(result, SymNodeVariable):
                    if result.evaluate_expr():
                        if push:
                            self.push(value)
                        self.jump(inst)
                else:
                    unimplemented(
                        gb_type="Data-dependent branching with non-constant __bool__",
                        context=f"method: {x}, result: {result}",
                        explanation="Attempted to perform data-dependent branching on a user-defined "
                        "object with a __bool__ method that did not return a constant.",
                        hints=[],
                    )
            # __bool__ or __len__ is non-function or not existed in the user defined object
            else:
                if truth_fn(True):
                    if push:
                        self.push(value)
                    self.jump(inst)
        elif not value.is_tensor() and value.has_unpack_var_sequence(self):
            if truth_fn(len(value.unpack_var_sequence(self))):
                if push:
                    self.push(value)
                self.jump(inst)
        elif isinstance(value, SymNodeVariable):
            try:
                # if the user is branching on a SymBool, guard on it
                # if the user has code like:
                #    if size:
                #        ...
                # then they are just testing truthiness: guard that the expr != 0
                if isinstance(value.sym_num, torch.SymBool):
                    eval_result = value.evaluate_expr(self.output)
                else:
                    eval_result = guard_bool(value.sym_num != 0)
            except exc.UserError as e:
                if self.should_compile_partial_graph():
                    return jump_graph_break(self, inst, value, extra_msg=f"\n{e}")
                raise
            if truth_fn(eval_result):
                if push:
                    self.push(value)
                self.jump(inst)
        elif isinstance(value, variables.BackwardHookVariable):
            if truth_fn(True):
                if push:
                    self.push(value)
                self.jump(inst)
        else:
            from .source import is_constant_source

            if value.source is not None and is_constant_source(value.source):
                if truth_fn(value.get_real_value()):  # type: ignore[attr-defined]
                    if push:
                        self.push(value)
                    self.jump(inst)
            else:
                raise_jump_graph_break(value)