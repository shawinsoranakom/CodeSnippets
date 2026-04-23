def var_getattr(self, tx: "InstructionTranslator", name: str) -> VariableTracker:
        # [Note: __torch_function__] We currently only support attributes that are defined on
        # base tensors, custom attribute accesses will graph break.
        import torch

        # I think only `_base` is breaking because we aren't modelling view
        # relationship perfectly in some scenarios.
        if name in banned_attrs:
            unimplemented(
                gb_type="Unsupported tensor subclass attribute access",
                context=f"{name}",
                explanation="`torch.compile` currently can't trace this",
                hints=[
                    f"Avoid accessing {name} of tensor subclass in torch.compile region",
                    *graph_break_hints.SUPPORTABLE,
                ],
            )

        # Handle non-overridden attributes inherited from `torch.Tensor`.
        attr_is_overridden = _is_attr_overridden(tx, self, name)
        if (
            hasattr(torch.Tensor, name)
            and not attr_is_overridden
            and not inspect.ismethoddescriptor(getattr(torch.Tensor, name))
        ):
            args = [self]
            kwargs: dict[Any, Any] = {}
            if can_dispatch_torch_function(tx, args, kwargs):
                get_fn = VariableTracker.build(tx, getattr(torch.Tensor, name).__get__)

                return self.call_torch_function(
                    tx,
                    get_fn,
                    TupleVariable([self.class_type_var(tx)]),
                    args,
                    kwargs,
                )
        else:
            # `TensorVariable.var_getattr` doesn't handle user-defined
            # function/attribute well, so we explicitly handle them here.
            #
            # TODO move this logic into `TensorVariable`, or try to merge it
            # with similar logic in `UserDefinedObjectVariable`.
            try:
                attr = inspect.getattr_static(self.class_type, name)
            except AttributeError:
                pass
            else:
                import types

                cls_source = GlobalSource(self.global_mangled_class_name(tx))
                attr_source = AttrSource(cls_source, name)
                if isinstance(attr, types.FunctionType):
                    install_guard(attr_source.make_guard(GuardBuilder.CLOSURE_MATCH))
                    return UserMethodVariable(attr, self)

                elif isinstance(attr, property):
                    getter_source = AttrSource(attr_source, "fget")
                    getter = attr.fget
                    getter_var = VariableTracker.build(
                        tx, getter, source=getter_source, realize=True
                    )
                    return getter_var.call_function(tx, [self], {})

                elif isinstance(attr, classmethod):
                    return UserMethodVariable(
                        attr.__func__, self.class_type_var(tx), source=attr_source
                    )

                elif attr_is_overridden:
                    unimplemented(
                        gb_type="Unsupported tensor subclass overridden attribute access",
                        context=f"{name}",
                        explanation="`torch.compile` only support tracing certain types of overridden tensor subclass attributes",
                        hints=[
                            f"Avoid accessing {name} of tensor subclass in torch.compile region",
                            f"Renaming attribute `{name}` of type {self.class_type}",
                            *graph_break_hints.SUPPORTABLE,
                        ],
                    )

        return super().var_getattr(tx, name)