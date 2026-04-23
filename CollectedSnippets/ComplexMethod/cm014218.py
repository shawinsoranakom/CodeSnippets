def resolve_cls_descriptor(
        self,
        tx: "InstructionTranslator",
        name: str,
        cls_attr: object,
        source: Source | None,
    ) -> VariableTracker:
        """Handle descriptors found in cls.__mro__."""
        if isinstance(cls_attr, staticmethod):
            return VariableTracker.build(tx, cls_attr.__get__(self.value), source)

        if isinstance(cls_attr, classmethod):
            if isinstance(cls_attr.__func__, property):
                fget_vt = VariableTracker.build(tx, cls_attr.__func__.fget)
                return fget_vt.call_function(tx, [self], {})
            return variables.UserMethodVariable(cls_attr.__func__, self, source=source)

        if isinstance(cls_attr, types.ClassMethodDescriptorType):
            func = cls_attr.__get__(None, self.value)
            return VariableTracker.build(tx, func, source)

        # property and _tuplegetter accessed on the class return the
        # descriptor itself (descriptor.__get__(None, cls) is descriptor).
        # Build directly — no need to invoke __get__.
        if isinstance(cls_attr, (property, _collections._tuplegetter)):
            if source:
                return VariableTracker.build(tx, cls_attr, source)
            return UserDefinedObjectVariable(cls_attr)

        # Comparison dunders inherited from object — defer to runtime.
        if name in cmp_name_to_op_mapping and not isinstance(
            cls_attr, types.FunctionType
        ):
            return variables.GetAttrVariable(
                self, name, py_type=type(cls_attr), source=source
            )

        # User-defined descriptor with Python __get__.
        # For torch-internal classes or attributes in the class's own __dict__,
        # defer descriptor invocation to runtime via VariableTracker.build to
        # avoid compile-time side effects (e.g. deprecation warnings from
        # _ClassPropertyDescriptor on torch.FloatStorage.dtype).
        get_fn = inspect.getattr_static(type(cls_attr), "__get__", None)
        if isinstance(get_fn, types.FunctionType):
            if source and (
                name in getattr(self.value, "__dict__", {})
                or self.value.__module__.startswith("torch.")
                or self.value.__module__ == "torch"
            ):
                return VariableTracker.build(tx, cls_attr, source)
            return self.invoke_cls_descriptor_get(tx, name, cls_attr, source)

        # C-level descriptors (WrapperDescriptor, MethodDescriptor, etc.)
        # Build directly when the attribute lives in the class's own __dict__
        # or the class belongs to torch (needed for e.g. torch.Tensor.dim).
        # OrderedDict's C-level methods are handled at runtime.
        if inspect.ismethoddescriptor(cls_attr) or is_wrapper_or_member_descriptor(
            cls_attr
        ):
            if (
                source
                and self.value is not collections.OrderedDict
                and (
                    name in getattr(self.value, "__dict__", {})
                    or self.value.__module__.startswith("torch.")
                    or self.value.__module__ == "torch"
                )
            ):
                return VariableTracker.build(tx, cls_attr, source)
            return variables.GetAttrVariable(self, name, type(cls_attr), source=source)

        # Everything else: FunctionType, etc.
        return VariableTracker.build(tx, cls_attr, source)