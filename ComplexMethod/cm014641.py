def __init__(
        self,
        func: FunctionSchema,
        properties: LazyIrProperties | None = None,
        *,
        symint: bool,
    ) -> None:
        if properties:
            self.properties = properties

        self.func = func
        self.symint = symint
        positional_args: list[LazyArgument] = []
        for arg_field in ["pre_self_positional", "self_arg", "post_self_positional"]:
            if arg_field == "self_arg" and func.arguments.self_arg is not None:
                arg = func.arguments.self_arg.argument
                positional_args.append(
                    LazyArgument(arg, self.properties, symint=symint)
                )
            elif getattr(func.arguments, arg_field) is not None:
                positional_args.extend(
                    LazyArgument(arg, self.properties, symint=symint)
                    for arg in getattr(func.arguments, arg_field)
                )
        self.positional_args = tuple(positional_args)

        keyword_args: list[LazyArgument] = []
        for arg_field in [
            "pre_tensor_options_kwarg_only",
            "tensor_options",
            "post_tensor_options_kwarg_only",
            "out",
        ]:
            curr_args = getattr(func.arguments, arg_field)
            if curr_args is not None:
                if isinstance(curr_args, TensorOptionsArguments):
                    curr_args = curr_args.all()
                for arg in curr_args:
                    if isGeneratorType(arg.type):
                        if self.generator_arg is not None:
                            raise AssertionError(
                                "We expect there is only one generator arg"
                            )
                        self.generator_arg = NamedCType(
                            arg.name,
                            arg.type,  # type:ignore[arg-type]
                        )
                keyword_args.extend(
                    LazyArgument(arg, self.properties, symint=symint)
                    for arg in curr_args
                )
        self.keyword_args = tuple(keyword_args)
        self.name = func.name
        self.returns = func.returns