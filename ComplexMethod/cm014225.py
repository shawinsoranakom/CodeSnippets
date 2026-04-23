def call_function(
        self,
        tx: "InstructionTranslator",
        args: Sequence[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker:
        if (
            self.is_supported_random()
            and all(k.is_python_constant() for k in args)
            and all(v.is_python_constant() for v in kwargs.values())
        ):
            return call_random_fn(tx, self.value, args, kwargs)  # type: ignore[arg-type]
        elif istype(self.value, types.MethodType):
            func = self.value.__func__
            obj = self.value.__self__
            if (
                func is torch.utils._contextlib._DecoratorContextManager.clone
                and variables.TorchCtxManagerClassVariable.is_matching_cls(
                    obj.__class__
                )
                and not (args or kwargs)
            ):
                return variables.TorchCtxManagerClassVariable(
                    obj.__class__
                ).call_function(tx, args, kwargs)

            if (
                func is torch.autograd.grad_mode.inference_mode.clone
                and obj.__class__ is torch.autograd.grad_mode.inference_mode
            ):
                # simulate the inference_mode.clone implementation
                var = VariableTracker.build(tx, obj.mode)  # type: ignore[attr-defined]
                return variables.TorchCtxManagerClassVariable(
                    obj.__class__
                ).call_function(tx, [var], kwargs)

            if self.source is None:
                unimplemented(
                    gb_type="attempted to call sourceless user-defined object as a method",
                    context=f"object={self.value}, function={func}, args={args}, kwargs={kwargs}",
                    explanation="Dynamo does not support this.",
                    hints=[
                        f"Ensure the user-defined object {self.value} is constructed outside the compiled region.",
                    ],
                )
            assert self.source is not None
            func_src = AttrSource(self.source, "__func__")
            func_var = VariableTracker.build(tx, func, func_src, realize=True)
            obj_src = AttrSource(self.source, "__self__")
            obj_var = VariableTracker.build(tx, obj, obj_src)
            return func_var.call_function(tx, [obj_var] + args, kwargs)  # type: ignore[arg-type]
        elif callable(self.value):
            if self.source:
                assert self.cls_source is not None
                source_attr = AttrSource(self.cls_source, "__call__")
                install_guard(source_attr.make_guard(GuardBuilder.CLOSURE_MATCH))
            return self.call_method(tx, "__call__", args, kwargs)  # type: ignore[arg-type]

        return super().call_function(tx, args, kwargs)