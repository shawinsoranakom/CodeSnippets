def mp_subscript_impl(
        self,
        tx: "InstructionTranslator",
        key: "VariableTracker",
    ) -> "VariableTracker":
        # nn.Module containers (ModuleList/Dict/Sequential/ParameterDict/ParameterList)
        # These are Python-level __getitem__, not CPython C slots.
        # TODO(follow-up): add tests for ModuleList negative index, ModuleList/Sequential
        # slice, ModuleDict missing key, invalid key types
        from .lists import SliceVariable
        from .tensor import SymNodeVariable

        module = tx.output.get_submodule(self.module_key)

        builtin_supported = (
            torch.nn.ModuleDict.__getitem__,
            torch.nn.ModuleList.__getitem__,
            torch.nn.ParameterDict.__getitem__,
            torch.nn.ParameterList.__getitem__,
            torch.nn.Sequential.__getitem__,
        )
        # pyrefly: ignore[missing-attribute]
        if type(module).__getitem__ not in builtin_supported:
            if not (
                key.is_python_constant()
                and isinstance(key.as_python_constant(), (str, int))
            ):
                unimplemented(
                    gb_type="Invalid or non-const argument in nn.Module __getitem__",
                    context=f"mp_subscript_impl: {self} {key}",
                    explanation="Dynamo does not support calling "
                    f"method `__getitem__` of ``nn.Module`` {module} with a non-constant or non-(str, int) key.",
                    hints=["Use constant arguments of type str or int for __getitem__"],
                )
            fn = module.__getitem__.__func__  # pyrefly: ignore[missing-attribute]

            assert isinstance(fn, types.FunctionType)

            src = AttrSource(AttrSource(self.source, "__getitem__"), "__func__")  # type: ignore[arg-type]
            return tx.inline_user_function_return(
                variables.UserFunctionVariable(fn, source=src),
                [self, key],
                {},
            )

        if isinstance(key, SliceVariable):
            # TODO(anijain2305,export-team) - Remove this if condition when inlining of inbuilt nn modules is
            # enabled for export.
            if tx.output.export:
                result = []
                keys = list(range(len(module)))[key.as_python_constant()]  # type: ignore[arg-type]
                for idx, submod in enumerate(module[key.as_python_constant()]):  # type: ignore[arg-type]
                    k = keys[idx]
                    src = NNModuleSource(GetItemSource(self.source, k))
                    result.append(
                        tx.output.register_attr_or_module(
                            submod,
                            k,
                            source=src,
                        )
                    )

                new_module = module[key.as_python_constant()]  # type: ignore[index]
                new_module_variable = tx.output.register_attr_or_module(
                    new_module,
                    f"{self}.__getitem__(slice)",
                    source=NNModuleSource(
                        GetItemSource(self.source, key.as_python_constant())
                    ),
                )
                return new_module_variable
            else:
                # slice on nn module results in a creation of new module instance, so we need to make it sourceless.
                # Convert to unspecialized so that UnspecializedNNModule variable can take care of it.
                self.convert_to_unspecialized(tx)

        key_value = 0
        if isinstance(key, SymNodeVariable):
            key_value = key.evaluate_expr(tx.output)
        elif key.is_python_constant():
            key_value = key.as_python_constant()
        else:
            unimplemented(
                gb_type="Unsupported key type for nn.Module.__getitem__",
                context=f"mp_subscript_impl: {self} {key}",
                explanation="Dynamo does not support getitem on "
                "`nn.Module` with non-constant key.",
                hints=[],
            )

        submod = module[key_value]  # type: ignore[index]
        return tx.output.register_attr_or_module(
            submod,
            self.module_key,
            key_value,
            source=NNModuleSource(GetItemSource(self.source, key_value)),
        )