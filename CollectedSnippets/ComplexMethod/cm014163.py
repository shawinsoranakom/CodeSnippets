def _call_getattr(
        self,
        tx: "InstructionTranslator",
        args: Sequence[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker:
        obj = args[0]
        name_var = args[1]
        default = args[2] if len(args) > 2 else None

        if not name_var.is_python_constant():
            unimplemented(
                gb_type="getattr() with non-constant name argument",
                context=f"getattr({obj}, {name_var}, {default})",
                explanation="getattr() with non-constant name argument is not supported",
                hints=["Ensure the name argument of getattr() is a string"],
            )

        name = name_var.as_python_constant()

        # See NOTE [Tensor "grad" and "_grad" attr]
        if obj.is_tensor() and name == "_grad":
            name = "grad"

        if tx.output.side_effects.is_attribute_mutation(obj):
            if isinstance(obj, variables.UnspecializedNNModuleVariable):
                if (
                    name
                    in (
                        "named_parameters",
                        "parameters",
                        "named_buffers",
                        "buffers",
                        "named_modules",
                        "modules",
                    )
                    and obj.is_state_mutated
                    and tx.output.side_effects.has_pending_mutation(obj)
                ):
                    unimplemented(
                        gb_type="getattr() on nn.Module with pending mutation",
                        context=f"getattr({obj}, {name}, {default})",
                        explanation="Intentionally graph breaking on getattr() on a nn.Module "
                        "with a pending mutation",
                        hints=[],
                    )

        if tx.output.side_effects.has_pending_mutation_of_attr(obj, name):
            return tx.output.side_effects.load_attr(obj, name)

        if default is not None:
            hasattr_var = obj.call_obj_hasattr(tx, name)
            if hasattr_var is not None:
                assert hasattr_var.is_constant_match(True, False)
                if not hasattr_var.as_python_constant():
                    return default
            else:
                return default

        source = obj.source and AttrSource(obj.source, name)
        if name in {"__bases__", "__base__", "__flags__"}:
            try:
                value = obj.as_python_constant()
                if isinstance(value, type):
                    if name == "__bases__":
                        tuple_args = [
                            VariableTracker.build(
                                tx, b, source and GetItemSource(source, i)
                            )
                            for i, b in enumerate(value.__bases__)
                        ]
                        return variables.TupleVariable(tuple_args, source=source)
                    if name == "__base__":
                        return VariableTracker.build(tx, value.__base__, source)
                    if name == "__flags__":
                        return VariableTracker.build(tx, value.__flags__)
            except NotImplementedError:
                pass

        if isinstance(obj, variables.NNModuleVariable):
            return obj.var_getattr(tx, name)
        elif isinstance(
            obj,
            (
                variables.TensorVariable,
                variables.NamedTupleVariable,
                variables.ConstantVariable,
                variables.DefaultDictVariable,
                variables.DistributedVariable,
                variables.UserDefinedClassVariable,
                variables.UserDefinedObjectVariable,
            ),
        ):
            if (
                isinstance(obj, variables.UserDefinedObjectVariable)
                and issubclass(obj.value.__class__, unittest.TestCase)
                and config.enable_trace_unittest
                and name
                in (
                    "assertRaisesRegex",
                    "assertNotWarns",
                    "assertWarnsRegex",
                    "assertWarns",
                )
            ):
                unimplemented(
                    gb_type="Failed to trace unittest method",
                    context=f"function: unittest.TestCase.{name}",
                    explanation=f"Dynamo does not know how to trace unittest method `{name}` ",
                    hints=[
                        f"Avoid calling `TestCase.{name}`. "
                        "Please report an issue to PyTorch.",
                    ],
                )
            if obj.is_tensor():
                # pyrefly: ignore[missing-attribute]
                fake_val = obj.as_proxy().node.meta["example_value"]
                if (
                    isinstance(fake_val, torch.Tensor)
                    and is_sparse_any(fake_val)
                    and (not tx.export or not config.capture_sparse_compute)
                ):
                    unimplemented(
                        gb_type="Attempted to wrap sparse Tensor",
                        context="",
                        explanation="torch.compile does not support sparse Tensors",
                        hints=[*graph_break_hints.SPARSE_TENSOR],
                    )

            try:
                return obj.var_getattr(tx, name)
            except AsPythonConstantNotImplementedError:
                # dont fallback on as_python_constant error because this leads
                # to a failure later on, and leads to a wrong stacktrace
                raise
            except NotImplementedError:
                return variables.GetAttrVariable(obj, name, source=source)
        elif isinstance(obj, variables.TorchInGraphFunctionVariable):
            # Get OpOverload from an OpOverloadPacket, e.g., torch.ops.aten.add.default.
            try:
                member = getattr(obj.value, name)
            except AttributeError:
                raise_observed_exception(AttributeError, tx)
                raise

            if isinstance(
                member, (torch._ops.OpOverloadPacket, torch._ops.OpOverload)
            ) and torch._dynamo.trace_rules.is_aten_op_or_tensor_method(member):
                return variables.TorchInGraphFunctionVariable(member, source=source)
            else:
                return variables.GetAttrVariable(obj, name, source=source)
        elif isinstance(obj, DummyModule):
            # TODO(mlazos) - Do we need this?
            if obj.is_torch or name not in obj.value.__dict__:
                member = getattr(obj.value, name)
            else:
                member = obj.value.__dict__[name]

            if config.replay_record_enabled:
                tx.exec_recorder.record_module_access(obj.value, name, member)  # type: ignore[arg-type, union-attr]
            return VariableTracker.build(tx, member, source)
        else:
            try:
                return obj.var_getattr(tx, name)
            except NotImplementedError:
                return variables.GetAttrVariable(obj, name, source=source)