def make_type_handlers() -> dict[
        type, Callable[["InstructionTranslator", Any], VariableTracker]
    ]:
        create = SourcelessBuilder.create
        handlers: dict[
            type, Callable[[InstructionTranslator, Any], VariableTracker]
        ] = {}
        for t in common_constant_types:
            handlers[t] = lambda tx, value: ConstantVariable(value)
        handlers[set] = lambda tx, value: SetVariable(
            [create(tx, x) for x in value], mutation_type=ValueMutationNew()
        )
        handlers[OrderedSet] = lambda tx, value: OrderedSetVariable(
            [create(tx, x) for x in value], mutation_type=ValueMutationNew()
        )
        handlers[dict] = lambda tx, value: ConstDictVariable(
            {create(tx, k): create(tx, v) for k, v in value.items()},
            type(value),
            mutation_type=ValueMutationNew(),
        )
        handlers[list] = lambda tx, value: ListVariable(
            [create(tx, x) for x in value], mutation_type=ValueMutationNew()
        )
        handlers[tuple] = lambda tx, value: TupleVariable(
            [create(tx, x) for x in value]
        )
        handlers[torch.Size] = lambda tx, value: SizeVariable(
            [create(tx, x) for x in value]
        )
        handlers[collections.OrderedDict] = handlers[dict]
        handlers[immutable_dict] = handlers[dict]
        handlers[immutable_list] = handlers[list]
        # Sourceless MappingProxyType object can be encountered while tracing
        # type.__dict__["__dict__"].__get__
        handlers[types.MappingProxyType] = lambda tx, value: MappingProxyVariable(
            ConstDictVariable(
                {create(tx, k): create(tx, v) for k, v in value.items()},
                dict,
                mutation_type=ValueMutationNew(),
            ),
        )
        handlers[types.GetSetDescriptorType] = (
            lambda tx, value: GetSetDescriptorVariable(value)
        )
        handlers[inspect.Parameter] = lambda tx, value: UserDefinedObjectVariable(
            value, mutation_type=ValueMutationNew()
        )
        handlers[random.Random] = lambda tx, value: RandomClassVariable()
        handlers[types.ModuleType] = lambda tx, value: PythonModuleVariable(value)

        handlers[torch.DispatchKeySet] = lambda tx, value: DispatchKeySetVariable(
            value, mutation_type=ValueMutationNew()
        )
        handlers[torch._functorch.pyfunctorch.FuncTorchInterpreter] = (
            lambda tx, value: FuncTorchInterpreterVariable(
                value, mutation_type=ValueMutationNew()
            )
        )

        handlers[torch.distributions.constraints._Real] = (
            lambda tx, value: UserDefinedObjectVariable(
                value, mutation_type=ValueMutationNew()
            )
        )
        handlers[torch.distributions.constraints._Interval] = (
            lambda tx, value: UserDefinedObjectVariable(
                value, mutation_type=ValueMutationNew()
            )
        )
        handlers[torch.distributions.constraints.Constraint] = (
            lambda tx, value: UserDefinedObjectVariable(
                value, mutation_type=ValueMutationNew()
            )
        )

        def passthrough(tx: "InstructionTranslator", value: T) -> T:
            return value

        for cls in VariableTrackerMeta.all_subclasses:
            handlers[cls] = passthrough
        return handlers