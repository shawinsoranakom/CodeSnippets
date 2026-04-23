def call_apply(
        self,
        tx: "InstructionTranslator",
        args: list[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker:
        requires_grad = False

        def visit(vt: VariableTracker) -> None:
            nonlocal requires_grad
            if vt.is_tensor():
                # type: ignore[attr-defined]
                if vt.requires_grad is not False:
                    requires_grad = True
            if isinstance(vt, variables.NNModuleVariable):
                if vt.is_training(tx):
                    requires_grad = True

        VariableTracker.visit(visit, (args, kwargs))

        if requires_grad and torch.is_grad_enabled():
            source = self.source

            from torch._functorch.autograd_function import (
                autograd_function_forward_rewritten,
            )
            from torch.autograd.function import _is_setup_context_defined

            forward_fn = self.fn_cls.forward

            is_setup_ctx_defined = _is_setup_context_defined(self.fn_cls.setup_context)
            if is_setup_ctx_defined:
                # If setup_context is defined, we generate a new forward function which includes
                # the original forward and setup_context function, and trace the new forward function.
                forward_fn = autograd_function_forward_rewritten(
                    self.fn_cls.forward, self.fn_cls.setup_context
                )
                # The forward points to a new function now, so we can't use the
                # old source. Later on, we guard specifically on
                # is_setup_ctx_defined
                source = None

            vjp_fn = self.fn_cls.vjp  # type: ignore[attr-defined]
            if vjp_fn is not torch.autograd.Function.vjp:
                unimplemented(
                    gb_type="Unsupported custom vjp",
                    context=f"call_apply {self} {args} {kwargs}",
                    explanation="Dynamo does not support tracing "
                    "`torch.autograd.Function` subclasses that define "
                    "a custom `vjp` method.",
                    hints=[
                        "Remove the custom `vjp` method if possible.",
                        "Use standard `backward` instead if applicable.",
                        *graph_break_hints.SUPPORTABLE,
                    ],
                )

            jvp_fn = self.fn_cls.jvp  # type: ignore[attr-defined]
            if jvp_fn is not torch.autograd.Function.jvp:
                unimplemented(
                    gb_type="Unsupported custom jvp",
                    context=f"call_apply {self} {args} {kwargs}",
                    explanation="Dynamo does not support tracing "
                    "`torch.autograd.Function` subclasses that define "
                    "a custom `jvp` method.",
                    hints=[
                        "Remove the custom `jvp` method if possible.",
                        *graph_break_hints.SUPPORTABLE,
                    ],
                )

            from .higher_order_ops import AutogradFunctionApplyVariable

            if source is None and not is_setup_ctx_defined:
                source = AttrSource(
                    tx.import_source(self.fn_cls.__module__), self.fn_cls.__name__
                )
            apply_source = source and AttrSource(source, member="apply")
            val = AutogradFunctionApplyVariable(
                forward_fn,
                self.fn_cls.backward,
                source,
                source=apply_source,
            ).call_function(tx, args, kwargs)
            if self.source and is_setup_ctx_defined:
                fwd_src = AttrSource(self.source, "forward")
                install_guard(fwd_src.make_guard(GuardBuilder.CLOSURE_MATCH))
                setup_ctx_src = AttrSource(self.source, "setup_context")
                install_guard(setup_ctx_src.make_guard(GuardBuilder.CLOSURE_MATCH))

            return val

        if self.source:
            source = AttrSource(self.source, "forward")
        else:
            source = None

        fn = self.fn_cls.forward
        ctx = AutogradFunctionContextVariable.create(tx, args, kwargs)
        args = [ctx, *args]
        if isinstance(fn, types.FunctionType):
            sig = inspect.signature(fn)
            if len(args) - 1 == len(sig.parameters):
                args = args[1:]  # Don't use context
            fn_vt = VariableTracker.build(tx, fn, source=source, realize=True)
            return fn_vt.call_function(tx, args, kwargs)
        elif isinstance(fn, types.MethodType):
            return variables.UserMethodVariable(
                fn.__func__,
                variables.UserDefinedClassVariable(self.fn_cls),
                source=source,
            ).call_function(tx, args, kwargs)
        else:
            unimplemented(
                gb_type="Non-function or method in subclass of torch.autograd.Function",
                context=f"call_apply {self} {args} {kwargs}",
                explanation="Dynamo requires the `forward` attribute of a "
                "`torch.autograd.Function` subclass to be a standard Python "
                f"function or method. Found type `{type(fn).__name__}` instead.",
                hints=[
                    "Ensure the `forward` method is defined as a regular "
                    "function or instance method."
                ],
            )