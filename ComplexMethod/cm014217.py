def var_getattr(self, tx: "InstructionTranslator", name: str) -> VariableTracker:
        source = AttrSource(self.source, name) if self.source is not None else None

        # --- Dynamo-specific pre-checks ---

        # Wrap OrderedDict/defaultdict.fromkeys as GetAttrVariable so it's
        # handled uniformly in call_method().
        if (
            self.value in {collections.OrderedDict, collections.defaultdict}
            and name == "fromkeys"
        ):
            return super().var_getattr(tx, name)

        # Custom metaclasses that override __getattribute__ replace the entire
        # lookup algorithm; bail out for those. Standard metaclasses (ABCMeta,
        # EnumType, etc.) that don't override __getattribute__ use
        # type.__getattribute__ which is the algorithm we implement below.
        metacls = type(self.value)
        if metacls is not type and "__getattribute__" in metacls.__dict__:
            unimplemented(
                gb_type="Custom metaclass with __getattribute__",
                context=f"type({self.value}) = {metacls}",
                explanation="Dynamo does not trace attribute access on classes whose "
                "metaclass overrides __getattribute__",
                hints=graph_break_hints.SUPPORTABLE,
            )

        # ---- CPython type_getattro algorithm ----
        # https://github.com/python/cpython/blob/3.13/Objects/typeobject.c#L5417-L5505
        # 1. meta_attr = lookup name in type(cls).__mro__  (metaclass chain)
        # 2. if meta_attr is a DATA descriptor → invoke
        # 3. cls_attr = lookup name in cls.__mro__  (class chain)
        # 4. if cls_attr has __get__ → invoke cls_attr.__get__(None, cls)
        # 5. if cls_attr exists (plain) → return as-is
        # 6. if meta_attr is a non-data descriptor or plain → return
        # 7. raise AttributeError

        # Step 1-2: Metaclass data descriptors.
        # For type(cls) is type, these are C-level getset/member descriptors
        # for __dict__, __mro__, __name__, __qualname__, __doc__, etc.
        meta_attr = self.lookup_metaclass_attr(name)
        if meta_attr is not NO_SUCH_SUBOBJ and is_data_descriptor(meta_attr):
            return self.resolve_meta_data_descriptor(tx, name, meta_attr, source)

        # Step 3-5: Class MRO lookup.
        cls_attr = self.lookup_cls_mro_attr(name)
        if cls_attr is not NO_SUCH_SUBOBJ:
            if hasattr(type(cls_attr), "__get__"):
                # Step 4: Descriptor — invoke __get__(None, cls).
                return self.resolve_cls_descriptor(tx, name, cls_attr, source)
            # Step 5: Plain attribute.
            return self.resolve_cls_plain_attr(tx, name, cls_attr, source)

        # Step 6: Metaclass non-data descriptor or plain attr.
        # These are non-data descriptors on the metaclass (e.g. type.__call__,
        # type.__subclasses__, type.mro).  We use GetAttrVariable to defer to
        # runtime rather than VariableTracker.build, because build would create
        # a variable for the raw C-level descriptor which then fails when
        # called (e.g. type.__subclasses__ is a method_descriptor that dynamo
        # can't trace).  GetAttrVariable defers the access and lets
        # call_method handle it.
        if meta_attr is not NO_SUCH_SUBOBJ:
            return variables.GetAttrVariable(self, name, type(meta_attr), source=source)

        # __getattr__ on metaclass (not part of type_getattro proper —
        # CPython handles this via slot_tp_getattr_hook).
        metacls = type(self.value)
        if metacls is not type:
            meta_getattr = self.lookup_metaclass_attr("__getattr__")
            if meta_getattr is not NO_SUCH_SUBOBJ and isinstance(
                meta_getattr, types.FunctionType
            ):
                return variables.UserMethodVariable(meta_getattr, self).call_function(
                    tx, [variables.ConstantVariable.create(name)], {}
                )

        # Step 7: AttributeError.
        raise_observed_exception(
            AttributeError,
            tx,
            args=[f"type object '{self.value.__name__}' has no attribute '{name}'"],
        )