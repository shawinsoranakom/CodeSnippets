def call_id(
        self, tx: "InstructionTranslator", *args: VariableTracker
    ) -> VariableTracker:
        if len(args) > 0 and isinstance(args[0], variables.NNModuleVariable):
            nn_mod_variable = args[0]
            mod = tx.output.get_submodule(nn_mod_variable.module_key)
            return VariableTracker.build(tx, id(mod))
        elif len(args) == 1 and args[0].is_tensor():
            tensor_variable = cast(TensorVariable, args[0])
            return tensor_variable.call_id(tx)
        elif istype(args[0], variables.FunctoolsPartialVariable):
            return VariableTracker.build(tx, id(args[0].fake_value))
        elif len(args) == 1:
            arg = args[0]
            if isinstance(
                arg,
                (
                    variables.UserDefinedClassVariable,
                    variables.UserDefinedObjectVariable,
                ),
            ):
                if arg.source:
                    if isinstance(arg, variables.UserDefinedClassVariable):
                        install_guard(arg.source.make_guard(GuardBuilder.CLASS_MATCH))
                    else:
                        install_guard(arg.source.make_guard(GuardBuilder.ID_MATCH))
            real_val = arg.get_real_python_backed_value()
            if real_val is not NO_SUCH_SUBOBJ:
                return VariableTracker.build(tx, id(real_val))
            return FakeIdVariable(id(arg))
        else:
            unimplemented(
                gb_type="id() with unsupported args",
                context=str(args),
                explanation=f"Dynamo doesn't know how to trace id() call with args {args}",
                hints=[
                    "Supported args are Tensors, and functions/nn.Modules/user-defined objects "
                    "from outside the compiled region.",
                    *graph_break_hints.SUPPORTABLE,
                ],
            )