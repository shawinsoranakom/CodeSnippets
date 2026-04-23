def handle_check(
            self,
            tx: "InstructionTranslator",
            *args: VariableTracker,
            **kwargs: VariableTracker,
        ) -> VariableTracker:
            predicate_vt = None
            message_vt = None

            if args:
                predicate_vt = args[0]
                rest_args = args[1:]
            else:
                rest_args = ()

            if predicate_vt is None and "cond" in kwargs:
                predicate_vt = kwargs.pop("cond")

            if rest_args:
                message_vt = rest_args[0]
            elif "message" in kwargs:
                message_vt = kwargs.pop("message")

            if predicate_vt is None:
                return wrap_fx_proxy(
                    tx=tx,
                    proxy=tx.output.create_proxy(
                        "call_function",
                        self.value,
                        (),
                        {},
                    ),
                )

            message_eager = None
            message_graph_proxy = None
            if message_vt is not None:
                if (
                    not isinstance(message_vt, NestedUserFunctionVariable)
                    or message_vt.has_closure()
                ):
                    unimplemented(
                        gb_type="Can't extract message from torch._check()",
                        context=str(message_vt),
                        explanation=(
                            "The second argument of torch._check() must be a function "
                            "defined within the torch.compile region "
                            "that does not reference a non-local variable."
                        ),
                        hints=[
                            "Make sure the message function is defined in the torch.compile region.",
                            "Remove any closure variables, e.g. "
                            "remove references to closure variable `x` in `lambda: f'{x} failed check'`",
                            *graph_break_hints.SUPPORTABLE,
                        ],
                    )
                message_eager = message_vt.get_function()

                message_graph_proxy = tx.output.register_static_attr_and_return_proxy(
                    "_check_message", message_eager
                )

            if predicate_vt.is_python_constant():
                self.value(predicate_vt.as_python_constant(), message_eager)
                return ConstantVariable.create(None)

            predicate_proxy = predicate_vt.as_proxy()

            proxy_args: tuple[Any, ...]
            if message_graph_proxy is None:
                proxy_args = (predicate_proxy,)
            else:
                proxy_args = (predicate_proxy, message_graph_proxy)

            return wrap_fx_proxy(
                tx=tx,
                proxy=tx.output.create_proxy(
                    "call_function",
                    self.value,
                    proxy_args,
                    {},
                ),
            )