def call_method(
        self,
        tx: "InstructionTranslator",
        name: str,
        args: list[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker:
        inner_fn, source = self._resolved_getattr_and_source(tx, name)
        assert self.objvar is not None
        # This essentially simulates CPython's `super_getattro`:
        # https://github.com/python/cpython/blob/a1c52d1265c65bcf0d9edf87e143843ad54f9b8f/Objects/typeobject.c#L11138-L11168
        # where `inner_fn` is the VT for `res = _super_lookup_descr(...)`.
        #
        # However, `res`'s type needs to be checked for `tp_descr_get`, and
        # applied if it has one. We currently don't have polyfills for all the
        # relevant `tp_descr_get`, so we explicitly handle the cases we care
        # about here (e.g., note the staticmethod, classmethod cases).
        if inner_fn is object.__init__:
            return LambdaVariable(identity)
        elif inner_fn is torch.nn.Module.__init__:
            objvar = self.objvar
            from ..side_effects import AttributeMutationNew

            if (
                isinstance(objvar, variables.UserDefinedObjectVariable)
                and isinstance(objvar.mutation_type, AttributeMutationNew)
                and not (args or kwargs)
            ):
                with do_not_convert_to_tracable_parameter():
                    fn_vt = VariableTracker.build(
                        tx, unpatched_nn_module_init, source=source
                    )
                    return fn_vt.call_function(tx, [self.objvar] + args, kwargs)
            else:
                unimplemented(
                    gb_type="Unsupported super().__init__() call",
                    context=f"call_method {self} {name} {args} {kwargs}",
                    explanation="Dynamo encountered a super().__init__() call "
                    f"on {objvar} that resolved to a `torch.nn.Module.__init__()` "
                    "call that we cannot trace.",
                    hints=[*graph_break_hints.DIFFICULT],
                )
        elif (
            self.objvar.source
            and hasattr(inner_fn, "__name__")
            and inner_fn.__name__ == "__new__"
            and variables.UserDefinedClassVariable.is_supported_new_method(inner_fn)
        ):
            user_cls = inner_fn.__self__
            if hasattr(user_cls, "__module__") and user_cls.__module__ == "builtins":
                user_cls_vt: VariableTracker = VariableTracker.build(tx, user_cls)
            else:
                assert source is not None
                user_cls_source = source.member
                user_cls_vt = variables.UserDefinedClassVariable(
                    user_cls, source=user_cls_source
                )
            return user_cls_vt.call_method(tx, "__new__", args, kwargs)
        elif isinstance(inner_fn, staticmethod) and isinstance(
            inner_fn.__func__, types.FunctionType
        ):
            fn_vt = VariableTracker.build(
                tx, inner_fn.__func__, source=source, realize=True
            )
            return fn_vt.call_function(tx, args, kwargs)
        elif isinstance(inner_fn, classmethod) and isinstance(
            inner_fn.__func__, types.FunctionType
        ):
            if isinstance(self.objvar, variables.UserDefinedClassVariable):
                # super().classmethod is called from a classmethod itself. So,
                # super was converted to super(__class__, cls) in bytecode and
                # therefore we have to propagate the cls.
                cls_variable = self.objvar
            else:
                # current function is an instance method, therefore super was
                # converted to super(__class__, self). We have to find
                # type(self) to bind the cls to the parent classmethod.
                # Note that it can't be the self.typevar because __class__ is
                # the class where the method is defined, which could be
                # different from type(self) with polymorphism.
                cls_source = None
                if self.objvar.source:
                    cls_source = TypeSource(self.objvar.source)
                cls_variable = VariableTracker.build(
                    tx,
                    self.objvar.value_type,  # type: ignore[attr-defined]
                    cls_source,
                )
            assert source is not None
            fn_vt = VariableTracker.build(
                tx,
                inner_fn.__func__,
                source=AttrSource(source, "__func__"),
                realize=True,
            )
            return fn_vt.call_function(tx, [cls_variable, *args], kwargs)
        elif isinstance(inner_fn, types.FunctionType):
            fn_vt = VariableTracker.build(tx, inner_fn, source=source, realize=True)
            return fn_vt.call_function(tx, [self.objvar] + args, kwargs)
        elif isinstance(inner_fn, types.MethodType):
            return variables.UserMethodVariable(
                inner_fn.__func__, self.objvar, source=source
            ).call_function(tx, args, kwargs)
        elif is_standard_setattr(inner_fn) and isinstance(
            self.objvar, UserDefinedObjectVariable
        ):
            # type: ignore[arg-type]
            return self.objvar.method_setattr_standard(tx, *args, **kwargs)
        elif inner_fn is object.__delattr__:
            attr = args[0]
            try:
                attr = attr.as_python_constant()
            except NotImplementedError as exc:
                unimplemented(
                    gb_type="Non-constant attribute given to `super().__delattr__()`",
                    context=f"call_method {self} {name}",
                    explanation="Dynamo requires the attribute name passed to "
                    "`super().__delattr__(...)` to be a constant (string).",
                    hints=[
                        "Ensure the attribute name is a string literal or a constant variable."
                    ],
                    from_exc=exc,
                )
            if not tx.output.side_effects.is_attribute_mutation(self.objvar):
                unimplemented(
                    gb_type="Attempted super().__delattr__() on an object without mutation tracking",
                    context=f"call_method {self} {name}",
                    explanation="Dynamo needs to track mutations on an object "
                    "before `super().__delattr__` can be used on it. But the "
                    f"object ({self.objvar}) doesn't have attribute mutation "
                    "tracking enabled.",
                    hints=[
                        "Ensure the object is tracked by Dynamo's side effect system.",
                        *graph_break_hints.DYNAMO_BUG,
                    ],
                )
            assert isinstance(attr, str)
            tx.output.side_effects.store_attr(
                self.objvar, attr, variables.DeletedVariable()
            )
            return variables.ConstantVariable.create(None)
        elif (
            isinstance(self.objvar, variables.UserDefinedObjectVariable)
            and self.objvar._base_vt is not None
            and self.objvar._base_methods is not None
            and inner_fn in self.objvar._base_methods
        ):
            return self.objvar._base_vt.call_method(tx, name, args, kwargs)
        elif inner_fn is object.__getattribute__:
            attr_name = args[0].value  # type: ignore[attr-defined]
            # object.__getattribute__ IS PyObject_GenericGetAttr.  Delegate
            # to the shared implementation so that __dict__, __class__,
            # polyfilled C descriptors, etc. are all handled consistently.
            if isinstance(self.objvar, UserDefinedObjectVariable):
                return self.objvar.generic_getattr(tx, attr_name)

            attr_value = None
            try:
                attr_value = object.__getattribute__(
                    self.objvar.value,  # pyrefly: ignore[missing-attribute]
                    attr_name,
                )
            except AttributeError:
                raise_observed_exception(AttributeError, tx)

            attr_source = None
            if self.objvar.source is not None:
                attr_source = GenericAttrSource(self.objvar.source, attr_name)
            return VariableTracker.build(tx, attr_value, attr_source)
        elif inner_fn is torch._C._disabled_torch_function_impl:
            # See `THPModule_disable_torch_function` for the C impl.
            # The signature of _disabled_torch_function_impl is similar to
            # `__torch_function__`, just without the first `cls` argument:
            #  * (func, types, args, kwargs)
            func = args[0]
            # pyrefly: ignore [implicit-any]
            tf_kwargs = {}
            tf_args = args[2].items  # type: ignore[attr-defined]
            # type: ignore[attr-defined]
            for hash_key_vt, value_vt in args[3].items.items():
                key_str = hash_key_vt.vt.as_python_constant()
                tf_kwargs[key_str] = value_vt

            tx_old = tx.symbolic_torch_function_state.torch_function_subclass_enabled
            tx.symbolic_torch_function_state.torch_function_subclass_enabled = False
            try:
                return func.call_function(tx, tf_args, tf_kwargs)
            finally:
                tx.symbolic_torch_function_state.torch_function_subclass_enabled = (
                    tx_old
                )
        elif (
            isinstance(inner_fn, types.MethodDescriptorType)
            and inner_fn in trace_rules.get_tensor_method()
        ):
            # FunctionType but implementation is in C, we support some of these,
            # e.g., tensor ops like `torch.Tensor.to`.
            fn_var = VariableTracker.build(tx, inner_fn, source, realize=True)
            return fn_var.call_function(tx, [self.objvar] + args, kwargs)

        unimplemented(
            gb_type="Attempted to call a super() attribute that is "
            "not a function or method",
            context=f"call_method {self} {name}",
            explanation="Dynamo does not know how to trace the call "
            f"`super().{name}()` because `super().{name}` is not a "
            "function or method attribute.",
            hints=[
                "Ensure the attribute accessed via `super()` is a standard method or function.",
            ],
        )