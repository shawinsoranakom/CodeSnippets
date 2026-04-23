def prepare_triton_wrapper_args(
        self, call_args: list[Any], arg_types: list[Any]
    ) -> tuple[list[Any], list[Any]]:
        assert len(call_args) == len(arg_types), (call_args, arg_types)
        new_args = []
        new_args_types = []
        for arg, arg_type in zip(call_args, arg_types):
            if isinstance(arg, str):
                if isinstance(arg_type, torch_dtype) and should_unwrap_unspec_arg(arg):
                    # dynamo wraps unspec variable as 0d CPU tensor, need convert to scalar
                    arg_type = UnwrapUnspecArg(dtype=arg_type)
                new_args.append(arg)
            elif isinstance(arg, bool):
                new_args.append(str(arg).lower())
            elif isinstance(arg, (int, float, SymbolicCallArg)):
                if isinstance(arg, float):
                    new_args.append(self.generate_float_value(arg))
                else:
                    new_args.append(str(arg))
            else:
                new_args.append(cexpr(V.graph.sizevars.simplify(arg)))
            new_args_types.append(arg_type)
        return new_args, new_args_types