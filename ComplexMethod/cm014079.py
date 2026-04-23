def call_method(
        self,
        tx: "InstructionTranslator",
        name: str,
        args: Sequence[VariableTracker],
        kwargs: dict[str, VariableTracker],
        constant: bool = False,
    ) -> VariableTracker:
        from . import ListIteratorVariable, TupleVariable
        from .constant import ConstantVariable

        key = self.module_key
        module = tx.output.get_submodule(key)

        def generic_call_method_helper(name: str) -> VariableTracker:
            # Helper function to put a `call_method` node in FX graph,
            # with nn.Module as the first arg.
            mod_proxy = tx.output.create_proxy(
                "get_attr",
                self.module_key,
                (),
                {},
            )
            set_example_value(mod_proxy.node, module)

            proxy_args, proxy_kwargs = proxy_args_kwargs(args, kwargs)

            from .builder import wrap_fx_proxy

            return wrap_fx_proxy(
                tx=tx,
                proxy=tx.output.create_proxy(
                    "call_method",
                    name,
                    args=(mod_proxy, *proxy_args),
                    kwargs=proxy_kwargs,
                ),
            )

        if name in ["_call_impl", "_wrapped_call_impl"]:
            # Example: `self.layer.__call__(x)`
            # This is used for explicit calling `__call__` in a forward function.
            # Dynamo inlines `__call__`, includes hooks.
            return self.call_function(tx, args, kwargs)
        elif name == "forward":
            # Example: `self.layer.forward(x)`
            # This is used for explicit calling `forward` in a forward function.
            # Dynamo puts `call_method` node in FX, doesn't trigger hooks.
            with record_nn_module_stack(
                self.module_key, self.get_nn_module_stack_source(), tx, module
            ):
                return generic_call_method_helper(name)

        if name == "_check_input_dim" and trace_rules.is_torch_inline_allowed(
            inspect.getfile(module.__class__._check_input_dim)  # type: ignore[union-attr]
        ):
            return ConstantVariable.create(True)

        if name == "_get_item_by_idx":
            if not args[1].is_python_constant():
                raise_type_error(
                    tx,
                    f"``nn.Module`` {module}'s call method {name} requires a constant index argument",
                )
            if not isinstance(args[0], TupleVariable):
                raise_type_error(
                    tx,
                    f"``nn.Module`` {module}'s call method {name} requires a tuple as first argument",
                )
            mod_var = args[0].items[args[1].value]  # type: ignore[attr-defined]
            if isinstance(mod_var, UnspecializedNNModuleVariable):
                return mod_var
            key = mod_var.module_key  # type: ignore[attr-defined]
            submod = tx.output.get_submodule(key)
            return tx.output.register_attr_or_module(
                submod,
                key,
                key,
                source=NNModuleSource(GetItemSource(self.source, key)),
            )

        if constant:
            fn = getattr(module, name)
            name = f"{module.__class__.__name__}_{name}_result"
            return invoke_and_store_as_constant(tx, fn, name, args, kwargs)

        def assert_all_args_kwargs_const() -> None:
            if not all(
                x.is_python_constant() for x in itertools.chain(args, kwargs.values())
            ):
                unimplemented(
                    gb_type="non-const argument in nn.Module method",
                    context=f"call_method: {self} {name} {args} {kwargs}",
                    explanation="Dynamo does not support calling "
                    f"method `{name}` of ``nn.Module`` {module} with non-constant arguments.",
                    hints=[],
                )

        def get_kwargs(*names: str) -> dict[str, Any]:
            assert_all_args_kwargs_const()
            fn = getattr(module, name)
            bound_args = inspect.signature(fn).bind(
                *([x.as_python_constant() for x in args]),
                **{k: v.as_python_constant() for k, v in kwargs.items()},
            )
            bound_args.apply_defaults()
            bound_args = bound_args.arguments
            return {k: bound_args[k] for k in names}

        def wrap_values(
            items: Iterable[tuple[Any, Any]],
        ) -> "variables.ListIteratorVariable":
            named_children: list[VariableTracker] = []
            for name, submod in items:
                named_children.append(
                    tx.output.register_attr_or_module(
                        submod,
                        key,
                        name,
                        source=NNModuleSource(gen_source(self.source, name)),
                    )
                )
            return ListIteratorVariable(
                named_children, mutation_type=ValueMutationNew()
            )

        def named_embed(name: str, obj: Any) -> "variables.TupleVariable":
            return TupleVariable(
                [
                    VariableTracker.build(tx, name),
                    tx.output.register_attr_or_module(
                        obj,
                        key,
                        name,
                        source=NNModuleSource(gen_source(self.source, name)),
                    ),
                ]
            )

        def gen_source(source: Source, name: str) -> Source:
            name_split = name.split(".")
            if name_split[0] == "":
                return source
            while len(name_split) > 0:
                x = name_split.pop(0)
                source = AttrSource(source, x)
            return source

        if name == "named_children":
            tx.output.guard_on_key_order.add(AttrSource(self.source, "_modules"))
            if args or kwargs:
                raise_args_mismatch(
                    tx,
                    name,
                    "0 args and 0 kwargs",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )
            named_children: list[VariableTracker] = []
            for name, submod in module.named_children():
                named_children.append(named_embed(name, submod))
            return ListIteratorVariable(
                named_children, mutation_type=ValueMutationNew()
            )
        elif name == "named_parameters":
            tx.output.guard_on_key_order.add(AttrSource(self.source, "_parameters"))
            named_parameters: list[VariableTracker] = []
            for name, param in module.named_parameters(
                **get_kwargs("prefix", "recurse")
            ):
                named_parameters.append(named_embed(name, param))
            return ListIteratorVariable(
                named_parameters, mutation_type=ValueMutationNew()
            )
        elif name == "named_buffers":
            tx.output.guard_on_key_order.add(AttrSource(self.source, "_buffers"))
            named_buffers: list[VariableTracker] = []
            for name, buffer in module.named_buffers(
                **get_kwargs("prefix", "recurse", "remove_duplicate")
            ):
                named_buffers.append(named_embed(name, buffer))
            return ListIteratorVariable(named_buffers, mutation_type=ValueMutationNew())
        elif name == "named_modules":
            tx.output.guard_on_key_order.add(AttrSource(self.source, "_modules"))
            named_modules_list: list[VariableTracker] = []
            for name, submod in module.named_modules(
                **get_kwargs("memo", "prefix", "remove_duplicate")
            ):
                named_modules_list.append(named_embed(name, submod))
            return ListIteratorVariable(
                named_modules_list, mutation_type=ValueMutationNew()
            )
        elif name == "children":
            tx.output.guard_on_key_order.add(AttrSource(self.source, "_modules"))
            if args or kwargs:
                raise_args_mismatch(
                    tx,
                    name,
                    "0 args and 0 kwargs",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )
            return wrap_values(module.named_children())
        elif name == "modules":
            tx.output.guard_on_key_order.add(AttrSource(self.source, "_modules"))
            return wrap_values(module.named_modules())
        elif name == "parameters":
            tx.output.guard_on_key_order.add(AttrSource(self.source, "_parameters"))
            return wrap_values(module.named_parameters(**get_kwargs("recurse")))
        elif name == "buffers":
            tx.output.guard_on_key_order.add(AttrSource(self.source, "_buffers"))
            return wrap_values(module.named_buffers(**get_kwargs("recurse")))
        elif name == "keys":
            if args or kwargs:
                raise_args_mismatch(
                    tx,
                    name,
                    "0 args and 0 kwargs",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )
            result = []
            # pyrefly: ignore[not-iterable]
            for tmp in module:
                result.append(VariableTracker.build(tx, tmp))
            return ListIteratorVariable(result, mutation_type=ValueMutationNew())
        elif name == "values":
            if args or kwargs:
                raise_args_mismatch(
                    tx,
                    name,
                    "0 args and 0 kwargs",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )
            return wrap_values(module.items())  # type: ignore[operator]
        elif name == "items":
            if args or kwargs:
                raise_args_mismatch(
                    tx,
                    name,
                    "0 args and 0 kwargs",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )
            items_result: list[VariableTracker] = []
            for name, submod in module.items():  # type: ignore[operator]
                items_result.append(named_embed(name, submod))
            return ListIteratorVariable(items_result, mutation_type=ValueMutationNew())
        elif name == "__iter__":
            return ListIteratorVariable(
                self.unpack_var_sequence(tx), mutation_type=ValueMutationNew()
            )
        elif (
            name == "__contains__"
            and isinstance(module, (torch.nn.ModuleDict, torch.nn.ParameterDict))
            and args
            and args[0].is_python_constant()
        ):
            return VariableTracker.build(
                tx, args[0].as_python_constant() in module._modules
            )
        elif (
            name == "_get_abs_string_index"
            or (
                isinstance(module, torch.nn.modules.conv._ConvNd)
                and name == "_conv_forward"
            )
            or (
                isinstance(module, torch.nn.modules.conv._ConvTransposeNd)
                and name == "_output_padding"
            )
        ):
            # Inline the function
            fn = getattr(module, name).__func__
            fn_source = AttrSource(AttrSource(self.source, name), "__func__")  # type: ignore[arg-type]
            return tx.inline_user_function_return(
                variables.UserFunctionVariable(fn, source=fn_source),
                [self] + list(args),
                kwargs,
            )
        # A loose heuristic, but seems to be generally good before we drop into the
        # manual handling of inputs
        elif (
            name in module.__class__.__dict__
            and callable(module.__class__.__dict__[name])
            and all(x.is_tensor() for x in itertools.chain(args, kwargs.values()))
        ):
            return generic_call_method_helper(name)
        else:
            return super().call_method(tx, name, list(args), kwargs)