def resolve_type_attr(
        self,
        tx: "InstructionTranslator",
        name: str,
        type_attr: object,
        source: Source | None,
    ) -> VariableTracker:
        """Handle non-data descriptors and plain class attributes from the type MRO."""
        from ..mutation_guard import unpatched_nn_module_init

        if (
            type_attr is unpatched_nn_module_init
            or type_attr is torch.nn.Module.__init__
        ):
            type_attr = unpatched_nn_module_init

        can_use_mro_source = self.cls_source is not None and self.source is not None

        if isinstance(type_attr, staticmethod):
            # type_attr is the raw staticmethod wrapper from cls.__dict__
            # (not the unwrapped function).  We call __get__ to unwrap it,
            # but the *source* must go through __func__ on the descriptor
            # (not the resolved function) because the guard needs to watch
            # the descriptor object in the class dict, not the result.
            if can_use_mro_source:
                source = AttrSource(
                    self.get_source_by_walking_mro(tx, name), "__func__"
                )
            func = type_attr.__get__(self.value)
            return VariableTracker.build(tx, func, source)
        elif isinstance(type_attr, classmethod):
            source_fn = None
            if can_use_mro_source:
                source_fn = AttrSource(
                    self.get_source_by_walking_mro(tx, name), "__func__"
                )  # type: ignore[assignment]
            return variables.UserMethodVariable(
                type_attr.__func__,
                self.var_getattr(tx, "__class__"),
                source_fn=source_fn,
                source=source,
            )
        elif isinstance(type_attr, types.ClassMethodDescriptorType):
            func = type_attr.__get__(self.value, None)
            return VariableTracker.build(tx, func, source)
        elif is_lru_cache_wrapped_function(type_attr):
            return variables.WrapperUserMethodVariable(
                type_attr, "__wrapped__", self, source=source
            )
        elif isinstance(type_attr, types.FunctionType):
            while hasattr(type_attr, "_torchdynamo_inline"):
                type_attr = type_attr._torchdynamo_inline  # type: ignore[union-attr]
                source = AttrSource(source, "_torchdynamo_inline") if source else None
            # Function on the type MRO + not in instance dict → bound method.
            var_source = None
            if can_use_mro_source:
                var_source = self.get_source_by_walking_mro(tx, name)
            return variables.UserMethodVariable(
                type_attr, self, source_fn=var_source, source=source
            )
        # Check for a Python-level __get__ (non-data descriptor with traceable __get__).
        get_fn = inspect.getattr_static(type(type_attr), "__get__", None)
        if isinstance(get_fn, types.FunctionType):
            return self.invoke_descriptor_get(tx, name, type_attr, source)

        # C-level non-data descriptors / opaque callables — defer to runtime.
        # MethodDescriptorType: e.g. list.append (PyMethodDef)
        # WrapperDescriptorType: e.g. list.__add__ (slot wrappers)
        # MethodWrapperType: e.g. [].__add__ (bound slot wrappers)
        #
        # Exception: if the descriptor has a registered polyfill, return the
        # polyfill as a bound method so Dynamo can trace through it.
        if (
            isinstance(
                type_attr,
                (
                    types.MethodDescriptorType,
                    types.WrapperDescriptorType,
                    types.MethodWrapperType,
                ),
            )
            or torch._C._dynamo.utils.is_instancemethod(type_attr)  # type: ignore[attr-defined]
            or is_cython_function(type_attr)
        ):
            from .. import trace_rules

            if trace_rules.is_polyfilled_callable(type_attr):  # type: ignore[arg-type]
                from .functions import PolyfilledFunctionVariable

                polyfill_handlers = PolyfilledFunctionVariable._get_polyfill_handlers()
                wrapped: Any = polyfill_handlers.get(type_attr)  # type: ignore[arg-type]
                if wrapped is not None:
                    traceable_fn = wrapped.__torch_dynamo_polyfill__
                    return variables.UserMethodVariable(traceable_fn, self)
            return variables.GetAttrVariable(self, name, type(type_attr), source=source)

        # Plain class variable (or MethodType, C-level non-data descriptor
        # without __get__, etc.).
        if can_use_mro_source:
            source = self.get_source_by_walking_mro(tx, name)
        elif not source and self.cls_source is not None:
            source = AttrSource(self.cls_source, name)
        return VariableTracker.build(tx, type_attr, source)