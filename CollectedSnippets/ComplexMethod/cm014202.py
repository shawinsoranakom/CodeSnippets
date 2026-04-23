def call_method(
        self,
        tx: "InstructionTranslator",
        name: str,
        args: Sequence[VariableTracker],
        kwargs: "dict[str, VariableTracker]",
    ) -> VariableTracker:
        from .builder import SourcelessBuilder, VariableBuilder
        from .torch_function import can_dispatch_torch_function, dispatch_torch_function

        if self.is_strict_mode(tx) and name in self._strict_mode_banned_ops():
            unimplemented(
                gb_type="Illegal method invocation in strict mode",
                context=f"call_method {self} {name} {args} {kwargs}",
                explanation="Dynamo currently does not support this method "
                f"({name}) invocation in strict mode.",
                hints=[],
            )

        if name == "__deepcopy__":
            unimplemented(
                gb_type="Attempted to copy.deepcopy a tensor",
                context=f"copy.deepcopy({self})",
                explanation="Dynamo does not support copy.deepcopy() on tensors.",
                hints=[
                    "Avoid calling copy.deepcopy() on tensors inside compiled regions.",
                ],
            )

        # Only override builtin tensor methods
        # The user can manually add override handling
        # with a decorator for other methods (e.g. a dispatch subclass with other methods)
        static_attr = all_tensor_attrs.get(name, None)
        is_base_tensor_method = static_attr is not None

        if (
            can_dispatch_torch_function(tx, tuple([self] + list(args)), kwargs)
            and is_base_tensor_method
        ):
            if self.source:
                func_var = VariableBuilder(
                    tx, AttrSource(AttrSource(self.source, "__class__"), name)
                )(static_attr)
            else:
                func_var = SourcelessBuilder.create(tx, getattr(torch.Tensor, name))

            return dispatch_torch_function(
                tx, func_var, tuple([self] + list(args)), kwargs
            )

        """
        Dispatch to a method-specific handler defined below.  If the
        handler returns None (or doesn't exist) we put the method call
        in the graph.
        """

        # This is seen in inspect signature where we check if the value is a default value
        if name == "__eq__" and isinstance(args[0], UserDefinedClassVariable):
            return variables.ConstantVariable.create(False)

        if name == "wait":
            if args or kwargs:
                raise torch._dynamo.exc.InternalTorchDynamoError(
                    "`wait` and `wait_tensor` do not take any arguments"
                )
            from torch.distributed._functional_collectives import wait_tensor

            from .builder import wrap_fx_proxy

            return wrap_fx_proxy(
                tx,
                tx.output.create_proxy(
                    "call_function", wait_tensor, (self.as_proxy(),), {}
                ),
            )

        # For historical reasons, these ops decompose down to syntactically
        # invalid aten ops because they contain the python keyword `from`, see
        # discussions in #151432 for more details.
        # We graph break for now since this use case is uncommon.
        if name == "random_":
            unimplemented(
                gb_type="Tensor.random_ op",
                context=f"Tensor.{name}({args=}, {kwargs=})",
                explanation="This is currently not supported.",
                hints=[
                    "Use the out-of-place version of this op",
                    *graph_break_hints.SUPPORTABLE,
                ],
            )
        elif name == "uniform_" and "from" in kwargs:
            unimplemented(
                gb_type="Tensor.uniform_ op called with `from` keyword",
                context=f"Tensor.{name}({args=}, {kwargs=})",
                explanation="This is currently not supported.",
                hints=[
                    "Avoid using the `from` keyword.",
                    *graph_break_hints.SUPPORTABLE,
                ],
            )

        try:
            handler_method = getattr(self, f"method_{name}")
        except AttributeError:
            pass
        else:
            try:
                # Realize any LazyVariableTracker in kwargs before calling handler.
                realized_kwargs = {k: v.realize() for k, v in kwargs.items()}
                result = handler_method(tx, *args, **realized_kwargs)
                if result:
                    return result
            except TypeError as e:
                unimplemented(
                    gb_type="Unhandled args for method",
                    context=f"call_method {self} {name} {args} {kwargs}",
                    explanation="Dynamo encountered an error while calling "
                    f"the method `{name}`.",
                    hints=[],
                    from_exc=e,
                )

        # Guard against unknown methods reaching the generic proxy path.
        # For traceable wrapper subclasses (DTensor, NestedTensor), class_type
        # is torch.Tensor, so check the example_value's actual type instead.
        example_value = self.proxy.node.meta.get("example_value")
        check_type = (
            type(example_value) if example_value is not None else self.class_type
        )
        if not hasattr(check_type, name):
            unimplemented(
                gb_type="Unhandled tensor method",
                context=f"call_method {self} {name} {args} {kwargs}",
                explanation=f"Tensor method `{name}` is not defined on "
                f"{check_type.__name__} and does not have an explicit "
                "handler in TensorVariable.",
                hints=[*graph_break_hints.SUPPORTABLE],
            )

        from .builder import wrap_fx_proxy

        proxy = tx.output.create_proxy(
            "call_method",
            name,
            *proxy_args_kwargs([self, *args], kwargs),
        )

        # [Note: Inplace ops and VariableTracker metadata]
        # For inplace operations, we need to propagate tensor metadata from the
        # arguments to self. For example:
        #   x.add_(y) where y.requires_grad=True => x.requires_grad becomes True
        # We detect inplace ops by checking if self's fake tensor version changes
        # after wrap_fx_proxy (which runs get_fake_value internally).
        # We only synchronize when there's a tensor argument, since that's when
        # metadata propagation is relevant.
        version_before = self._get_fake_version()
        result = wrap_fx_proxy(tx, proxy)
        self._sync_if_inplace_mutation(
            tx, version_before, any(arg.is_tensor() for arg in args)
        )

        return result