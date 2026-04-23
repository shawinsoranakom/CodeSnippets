def call_method(
        self,
        tx: "InstructionTranslator",
        name: str,
        args: list[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker:
        assert hasattr(self.value, name), f"no stream method found named {name}"

        from ..utils import cmp_name_to_op_mapping, proxy_args_kwargs
        from .builder import wrap_fx_proxy_cls

        if name == "wait_event":
            event_arg = args[0]
            assert isinstance(event_arg, EventVariable)
            tx.output.create_proxy(
                "call_function",
                torch.ops.streams.wait_event,
                (event_arg.user_object_index, self.user_object_index),
                {},
            )
            return ConstantVariable.create(None)
        elif name == "wait_stream":
            other_stream = args[0]
            assert isinstance(other_stream, StreamVariable)
            tx.output.create_proxy(
                "call_function",
                torch.ops.streams.wait_stream,
                (self.user_object_index, other_stream.user_object_index),
                {},
            )
            return ConstantVariable.create(None)
        elif name == "synchronize":
            tx.output.create_proxy(
                "call_function",
                torch.ops.streams.synchronize_stream,
                (self.user_object_index,),
                {},
            )
            return ConstantVariable.create(None)
        elif name == "query":
            return wrap_fx_proxy_cls(
                target_cls=ConstantVariable,
                tx=tx,
                proxy=tx.output.create_proxy(
                    "call_method", name, *proxy_args_kwargs([self] + args, kwargs)
                ),
            )
        elif name == "record_event":
            from .builder import wrap_fx_proxy

            tx.output.check_event_record_after_input_mutation(id(self.value))
            if args and isinstance(args[0], EventVariable):
                event_var = args[0]
                event = event_var.value
                event_index = event_var.user_object_index
            else:
                event = self.value.record_event()
                event_index = register_graph_created_object(
                    event,
                    EventVariable.make_construct_in_graph_event_fn(
                        TupleVariable([]), ConstDictVariable({})
                    ),
                )
            tx.output.create_proxy(
                "call_function",
                torch.ops.streams.record_event,
                (event_index, self.user_object_index),
                {},
            )
            return wrap_fx_proxy(
                tx=tx,
                proxy=tx.output.create_proxy(
                    "call_function",
                    get_external_object_by_index,
                    (event_index,),
                    {},
                ),
            )
        elif name in cmp_name_to_op_mapping and len(args) == 1 and not kwargs:
            from ..guards import GuardBuilder, install_guard

            if self.source:
                install_guard(self.source.make_guard(GuardBuilder.EQUALS_MATCH))

            # NB : Checking for mutation is necessary because we compare
            # constant values
            other = args[0]
            if not isinstance(other, StreamVariable):
                return VariableTracker.build(tx, NotImplemented)

            if other.source:
                assert self.source is not None
                install_guard(self.source.make_guard(GuardBuilder.EQUALS_MATCH))
            return VariableTracker.build(
                tx,
                cmp_name_to_op_mapping[name](self.value, other.value),  # type: ignore[arg-type]
            )

        return super().call_method(tx, name, args, kwargs)