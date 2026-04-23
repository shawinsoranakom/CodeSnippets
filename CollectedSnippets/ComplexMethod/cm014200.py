def var_getattr(self, tx: "InstructionTranslator", name: str) -> VariableTracker:
        if self.is_strict_mode(tx):
            if name in self._strict_mode_banned_ops():
                unimplemented(
                    gb_type="Strict mode banned op",
                    context=f"var_getattr {self} {name}",
                    explanation=f"Getattr invocation '{name}' in strict mode is not supported.",
                    hints=[
                        f"Remove `{name}` from the list of banned ops by "
                        "setting `torch._dynamo.config._autograd_backward_strict_mode_banned_ops`.",
                    ],
                )
            elif name in self._strict_mode_conditional_banned_ops():
                raise UnknownPropertiesDuringBackwardTrace(
                    f"Unknown property {name} during speculating backward, dynamo will insert contiguous call ahead and speculate it again"
                )

        if name == "__class__":
            return VariableTracker.build(tx, self.python_type())

        handler = getattr(self, f"method_attr_{name}", None)
        result = handler(tx) if handler is not None else None

        # Add a guard for type matching, these guards are checked before tensor guards
        # In some cases, a <tensor>.<attr> guard can be evaluated first, and break if
        # <tensor> is later changed to another type
        if (
            result is not None
            and self.source
            and self.source.subguards_allowed()
            and not (
                name not in ("grad", "requires_grad") and result.is_python_constant()
            )
        ):
            install_guard(self.make_guard(GuardBuilder.TYPE_MATCH))
            result.source = AttrSource(self.source, name)

        # It's hard to get inplace view (metadata mutation) on graph input work properly across
        # dynamo/aot/inductor, just fall back.
        if self.source is not None and hasattr(torch.ops.aten, name):
            fn = getattr(torch.ops.aten, name)
            if (
                hasattr(fn, "overloads")
                and hasattr(fn, fn.overloads()[0])
                and torch.Tag.inplace_view in getattr(fn, fn.overloads()[0]).tags
            ):
                # Delay the graph break to the actual call of unsqueeze_/resize_/resize_as_ etc.
                return variables.misc.DelayGraphBreakVariable(
                    source=AttrSource(self.source, name),
                    msg="Getting an inplace view on a graph input is not supported",
                )

        # For attributes (not methods) that were not caught in the special handling above,
        # (e.g. tensor.real), we handle these generically, assuming that the output type is
        # a tensor.
        if result is None and name != "grad":

            def try_generic_attr_handling() -> VariableTracker | None:
                from .builder import wrap_fx_proxy
                from .misc import GetAttrVariable

                static_attr = all_tensor_attrs.get(name, None)
                if static_attr is None:
                    return None

                # Make sure this is an attribute, not a method.
                # type(torch.Tensor.H) should be "getset_descriptor"
                # This is a because of CPython implementation, see THPVariableType:
                # these attributes are implemented under tp_getset, which appear
                # as `getset_descriptor`s, (compared to, say, methods which appear
                # as `method_descriptor`s)
                if type(static_attr) is not types.GetSetDescriptorType:
                    return None

                proxy = GetAttrVariable.create_getattr_proxy(self.as_proxy(), name)
                if self.source is not None:
                    return wrap_fx_proxy(
                        tx=tx, proxy=proxy, source=AttrSource(self.source, name)
                    )
                else:
                    return wrap_fx_proxy(tx=tx, proxy=proxy)

            result = try_generic_attr_handling()

        if result is None:
            result = self.dynamic_getattr(tx, name)

        if result is None:
            raise NotImplementedError
        return result