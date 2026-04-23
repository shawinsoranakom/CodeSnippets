def call_function(
        self,
        tx: "InstructionTranslator",
        args: Sequence[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker:
        if is_tensor_base_attr_getter(self.method_wrapper) and isinstance(
            args[0], variables.TensorVariable
        ):
            if not (len(args) == 1 and len(kwargs) == 0):
                raise_type_error(
                    tx, "tensor attribute getter takes exactly one argument"
                )
            # type: ignore[arg-type, attr-defined]
            return args[0].var_getattr(tx, self.method_wrapper.__self__.__name__)

        # method-wrapper variables are common in __init__ calls. For example,
        # str("foo").__init__ is a method-wrapper. These method wrappers point
        # to C functions.  Here we intercept if these method-wrappers are from
        # builtins and then call the function counterpart directly by obtaining
        # the self object.
        self_obj = self.method_wrapper.__self__
        wrapper_name = self.method_wrapper.__name__
        # TODO(dynamo-team) - We can perhaps expand the scope to more names and
        # more builtins.
        if wrapper_name == "__init__":
            fn_obj = type(self_obj).__init__
            if fn_obj is object.__init__:
                return VariableTracker.build(tx, object).call_method(
                    tx,
                    wrapper_name,
                    # type: ignore[arg-type, list-item]
                    [self_obj, *args],
                    kwargs,
                )
        elif (
            sys.version_info >= (3, 14)
            # for some reason, even if the below check passes,
            # self.method_wrapper may not be the same as type.__dict__["__annotations__"].__get__
            and self_obj is type.__dict__["__annotations__"]
            and wrapper_name == "__get__"
        ):
            from .builder import SourcelessBuilder

            if len(args) == 1 and not kwargs:
                try:
                    return SourcelessBuilder.create(
                        tx, self.method_wrapper(args[0].as_python_constant())
                    )
                except AttributeError:
                    raise_observed_exception(AttributeError, tx)
                except AsPythonConstantNotImplementedError:
                    pass

            unimplemented(
                gb_type="unsupported type.__dict__['__annotations__'].__get__ call",
                context=f"call_function {self}, args: {args}, kwargs: {kwargs}",
                explanation="`torch.compile` only supports calling type.__dict__['__annotations__'].__get__ "
                "on a single constant argument (i.e. a type).",
                hints=[
                    "Make sure your call to type.__dict__['__annotations__'] only has "
                    "one positional argument (no keyword arguments).",
                    "Make sure the argument to type.__dict__['__annotations__'] is a constant "
                    "(i.e. type). For example, `object`, `int`, `MyCustomClass`.",
                    *graph_break_hints.SUPPORTABLE,
                ],
            )
        elif (self_obj is type.__dict__["__mro__"] and wrapper_name == "__get__") or (
            self_obj is type.__dict__["__dict__"] and wrapper_name == "__get__"
        ):
            attr_name = (
                "__mro__" if self_obj is type.__dict__["__mro__"] else "__dict__"
            )

            if len(args) == 1 and not kwargs:
                try:
                    value = self.method_wrapper(args[0].as_python_constant())
                except AsPythonConstantNotImplementedError:
                    pass
                else:
                    # Use a sourced variable when the descriptor is the
                    # standard one from type (not overridden by a metaclass).
                    source = args[0].source
                    if source is not None:
                        cls_val = args[0].as_python_constant()
                        static_desc = inspect.getattr_static(type(cls_val), attr_name)
                        if static_desc is self_obj:
                            if attr_name == "__mro__":
                                source = TypeMROSource(source)
                            else:
                                source = AttrSource(source, attr_name)
                            return VariableTracker.build(tx, value, source)

                    from .builder import SourcelessBuilder

                    return SourcelessBuilder.create(tx, value)

            unimplemented(
                gb_type=f"unsupported type.__dict__['{attr_name}'].__get__ call",
                context=f"call_function {self}, args: {args}, kwargs: {kwargs}",
                explanation=f"`torch.compile` only supports calling type.__dict__['{attr_name}'].__get__ "
                "on a single constant argument (i.e. a type).",
                hints=[
                    f"Make sure your call to type.__dict__['{attr_name}'].__get__ only has "
                    "one positional argument (no keyword arguments).",
                    f"Make sure the argument to type.__dict__['{attr_name}'].__get__ is a constant "
                    "(i.e. type). For example, `object`, `int`, `MyCustomClass`.",
                    *graph_break_hints.SUPPORTABLE,
                ],
            )

        return super().call_function(tx, args, kwargs)