def call_nn_parameter(
        cls,
        tx: "InstructionTranslator",
        data: Any | None = None,
        requires_grad: bool = True,
    ) -> VariableTracker:
        """A call to torch.nn.Parameter() gets lifted to before the graph"""
        if tx.export:
            unimplemented(
                gb_type="Attempted to use `torch.nn.Parameter()` with export",
                context="",
                explanation="Dynamo does not support this.",
                hints=[
                    "Do not use `torch.nn.Parameter()` with export.",
                    *graph_break_hints.SUPPORTABLE,
                ],
            )

        if isinstance(requires_grad, variables.VariableTracker):
            try:
                requires_grad = requires_grad.as_python_constant()
            except NotImplementedError:
                unimplemented(
                    gb_type="non-constant `requires_grad` argument to `torch.nn.Parameter`",
                    context=f"requires_grad={requires_grad}",
                    explanation="Dynamo does not support this.",
                    hints=[
                        "Change `requires_grad` to be a bool.",
                        *graph_break_hints.USER_ERROR,
                    ],
                )

        if data is None or not data.is_tensor():
            unimplemented(
                gb_type="`torch.nn.Parameter()` with unsupported data type",
                context=f"data={data}",
                explanation="Called `torch.nn.Parameter()` with non-Tensor argument.",
                hints=[
                    "Ensure the argument to `torch.nn.Parameter()` is a `torch.Tensor`.",
                    *graph_break_hints.USER_ERROR,
                ],
            )

        # this results in cleaner graphs, but only works for inputs
        if data.source:
            return cls._nn_param_via_prefix_insert(tx, data, requires_grad)

        if config.graph_break_on_nn_param_ctor:
            # Need user to manually move since we cannot
            unimplemented(
                gb_type="Attempted to use `torch.nn.Parameter()` constructor with Dynamo",
                context="",
                explanation="Dynamo does not support this",
                hints=[
                    "Try to construct `torch.nn.Parameter()` outside the compiled region.",
                    "If this is not possible, turn `graph_break_on_nn_param_ctor` off",
                    *graph_break_hints.SUPPORTABLE,
                ],
            )

        # TODO[@lucaskabela]: Remove the behavior below since it is deprecated
        if isinstance(
            data,
            TensorWithTFOverrideVariable,
        ) or is_traceable_wrapper_subclass_type(data.class_type):
            unimplemented(
                gb_type="Attempted to use torch.nn.Parameter constructor with tensor subclass",
                context=str(data),
                explanation="Dynamo does not support this.",
                hints=[
                    *graph_break_hints.SUPPORTABLE,
                ],
            )

        if not can_convert_to_tracable_parameter():
            unimplemented(
                gb_type="`torch.nn.Parameter`: cannot convert to traceable tracable",
                context="",
                explanation="convert_tracable_parameter is set to False.",
                hints=[
                    "Check usage of context manager: do_not_convert_to_tracable_parameter",
                    *graph_break_hints.DIFFICULT,
                ],
            )

        try:
            shape = tuple(data.var_getattr(tx, "shape").as_python_constant())
            dtype = data.var_getattr(tx, "dtype").as_python_constant()
            device = data.var_getattr(tx, "device").as_python_constant()
        except NotImplementedError as e:
            unimplemented(
                gb_type="`torch.nn.Parameter` with non-constant Tensor attributes",
                context=f"data={data}",
                explanation="Dynamo does not support this.",
                hints=[
                    "Ensure the Tensor argument's shape, dtype, and device are correct.",
                    *graph_break_hints.USER_ERROR,
                ],
                from_exc=e,
            )

        placeholder = tx.output.synthetic_graph_input(
            new_parameter_placeholder,
            (shape, dtype, device, requires_grad),
        )
        if data.requires_grad:
            data = data.call_method(tx, "detach", [], {})

        from .builder import wrap_fx_proxy

        result = wrap_fx_proxy(
            tx,
            tx.output.create_proxy(
                "call_function",
                tracable_create_parameter,
                (data.as_proxy(), placeholder.as_proxy()),
                {},
            ),
            # In reconstruct() we should use the original parameter. The one
            # returned by the graph will be an alias.
            source=placeholder.source,
        )
        assert result.is_tensor()
        result.class_type = torch.nn.Parameter  # type: ignore[union-attr]

        # TODO(jansel/bdhirsh) - There is some issue with
        # tracable_create_parameter. It does not seem to use the right
        # grad_enabled. Since this is parameter, we can just override the
        # has_grad_fn field to False to workaround the issue.
        result.has_grad_fn = False  # type: ignore[union-attr]

        # Register this parameter as a leaf tensor for backward() auto-detection.
        # When backward() is called without inputs, we need to find all leaf tensors,
        # including those created in-graph like nn.Parameter.
        tx.output.leaf_var_creation_order.append(result)

        # TODO(jansel): if the new param falls out of scope, currently it won't get freed until
        # the end of the graph.  We should fix this.
        return result