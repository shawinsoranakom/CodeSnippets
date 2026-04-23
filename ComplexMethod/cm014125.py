def create(tx: "InstructionTranslatorBase", value: Any) -> VariableTracker:
        value_type = type(value)
        # type: ignore[attr-defined]
        fast_handler = SourcelessBuilder._type_handlers.get(value_type)
        if fast_handler:
            return fast_handler(tx, value)

        if isinstance(value, VariableTracker):
            # This is always valid to call, and useful for recursive calls.
            return value
        elif (
            is_opaque_value_type(type(value))
            and not isinstance(value, enum.Enum)
            and not is_pybind11_enum_member(value)
        ):
            return TorchScriptObjectVariable.create(value, value)
        elif is_opaque_reference_type(type(value)):
            # This is for handling opaque objects in custom ops
            fake_script_obj = torch._library.fake_class_registry.maybe_to_fake_obj(
                tx.output.fake_mode, value
            )
            return TorchScriptObjectVariable.create(
                value,  # pyrefly: ignore[bad-argument-type]
                fake_script_obj,
            )
        # type: ignore[attr-defined]
        elif isinstance(value, dataclasses._HAS_DEFAULT_FACTORY_CLASS):
            return UserDefinedObjectVariable(value)
        elif ConstantVariable.is_literal(value):
            return ConstantVariable.create(value)
        elif callable(value) and trace_rules.lookup_callable(value) is not None:
            if trace_rules.is_callable_allowed(value):
                tx.output.has_user_defined_allowed_in_graph = True
            # pyrefly: ignore[not-callable, bad-argument-count]
            return trace_rules.lookup_callable(value)(value)
        elif callable(value) and UserDefinedClassVariable.is_supported_new_method(
            value
        ):
            # NamedTuple._make uses an alias of tuple.__new__
            # pyrefly: ignore[not-callable, bad-argument-count, missing-attribute]
            obj = trace_rules.lookup_callable(value.__self__)(value.__self__)
            return GetAttrVariable(obj, "__new__", py_type=type(value))
        elif is_function_or_wrapper(value):
            # pyrefly: ignore[not-callable, bad-argument-count]
            return trace_rules.lookup(value)(value)
        elif isinstance(
            value,
            (enum.Enum, torch.DispatchKey, torch._C._functorch.TransformType),
        ) or is_pybind11_enum_member(value):
            return UserDefinedObjectVariable(value)
        elif isinstance(value, (type, abc.ABCMeta)):
            if issubclass(type(value), type) and issubclass(value, BaseException):
                return UserDefinedExceptionClassVariable(value)
            return UserDefinedClassVariable(value)
        elif isinstance(value, types.MethodWrapperType):
            return MethodWrapperVariable(value)
        elif isinstance(value, types.MethodType):
            if isinstance(value.__self__, (type, abc.ABCMeta)):
                # value is a classmethod
                assert getattr(value.__self__, value.__func__.__name__) == value
                cls_obj_vt = SourcelessBuilder.create(tx, value.__self__)
                try:
                    # pyrefly: ignore[bad-argument-type]
                    return cls_obj_vt.var_getattr(tx, value.__func__.__name__)
                except NotImplementedError:
                    pass  # failthrough to unimplemented branch
            else:
                # Instance method — look up the VT for __self__ via side effects
                obj_vt = tx.output.side_effects.id_to_variable.get(id(value.__self__))
                if obj_vt is not None:
                    return torch._dynamo.variables.UserMethodVariable(
                        value.__func__, obj_vt
                    )
        elif isinstance(value, torch.fx.graph_module.GraphModule):
            return SourcelessGraphModuleVariable(value)
        elif isinstance(
            value, (importlib.machinery.ModuleSpec, torch.utils._pytree.TreeSpec)
        ):
            return UserDefinedObjectVariable(value)
        elif isinstance(value, re.Pattern):
            return ConstantLikeVariable(value)
        elif isinstance(value, torch._dynamo.variables.lazy.LazySymNodeFormatString):
            try:
                return ConstantVariable.create(str(value))
            # If we cannot create due to error in str() call, we should
            # try explicitly for string format variable
            except (
                torch._dynamo.exc.UserError,
                torch.fx.experimental.symbolic_shapes.GuardOnDataDependentSymNode,
            ):
                return StringFormatVariable.create(
                    value.fmt_var.as_python_constant(),
                    [value.sym_node_var],
                    {},
                )
        elif isinstance(value, type(torch._higher_order_ops.flex_attention_backward)):
            return torch._dynamo.variables.higher_order_ops.FlexAttentionBackwardHighOrderVariable(
                value
            )
        elif isinstance(value, (types.GenericAlias, types.UnionType)):
            return TypingVariable(value)
        elif is_namedtuple(value):
            output = [
                SourcelessBuilder.create(tx, getattr(value, name))
                for name in namedtuple_fields(type(value))
            ]
            tuple_vt = TupleVariable(output, mutation_type=ValueMutationNew())
            return UserDefinedTupleVariable.get_vt_cls(type(value))(
                value, tuple_vt=tuple_vt
            )
        elif (
            isinstance(value, torch.SymInt)
            and value.node.expr in tx.output.bound_symbols
        ):
            proxy = tx.output.bound_symbols[value.node.expr]
            return SymNodeVariable.create(tx, proxy)
        elif isinstance(value, slice):
            items = [
                SourcelessBuilder.create(tx, getattr(value, k))
                for k in ("start", "stop", "step")
            ]
            return SliceVariable(items, tx)  # pyrefly: ignore[bad-argument-type]
        elif istype(value, object):
            return ObjectVariable(value)
        unimplemented(
            gb_type="Unexpected type in sourceless builder",
            context=f"{value_type.__module__}.{value_type.__qualname__}",
            explanation=f"SourcelessBuilder.create does not know how to wrap {value_type}",
            hints=[*graph_break_hints.DYNAMO_BUG],
        )