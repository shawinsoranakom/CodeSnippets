def python_argdefs(
        self,
    ) -> tuple[list[ArgName], list[str], list[KernelArgType], list[Any]]:
        arg_defs: list[ArgName] = []
        call_args: list[str] = []
        arg_types: list[Any] = []
        precompile_args: list[KernelArgType] = []
        for inplaced in unique(self.inplace_buffers.values()):
            if isinstance(inplaced, RemovedArg):
                continue
            arg_defs.append(ArgName(inplaced.inner_name))
            call_args.append(inplaced.other_names[-1])
            arg_types.append(V.graph.get_dtype(inplaced.other_names[-1]))
            precompile_args.append(
                TensorArg(
                    name=inplaced.inner_name,
                    buffer=inplaced.other_names[-1],
                    dtype=V.graph.get_dtype(inplaced.other_names[-1]),
                )
            )
        for outer, inner in chain(
            self.input_buffers.items(),
            # pyrefly: ignore [bad-argument-type]
            self.output_buffers.items(),
        ):
            if outer in self.inplace_buffers or isinstance(inner, RemovedArg):
                continue
            arg_defs.append(ArgName(inner))
            call_args.append(outer)
            arg_types.append(V.graph.get_dtype(outer))
            precompile_args.append(
                TensorArg(
                    name=inner,
                    buffer=outer,
                    dtype=V.graph.get_dtype(outer),
                )
            )
        for outer, inner in self.sizevars.items():
            arg_defs.append(ArgName(inner))
            call_args.append(outer)
            arg_types.append(type(outer))
            precompile_args.append(SizeArg(inner, outer))
            if V.graph.wrapper_code:
                V.graph.wrapper_code.ensure_size_computed(outer)
        for arg in self.workspace_args:
            arg_defs.append(ArgName(arg.inner_name))
            call_args.append(arg.outer_name)
            precompile_args.append(arg)
            arg_types.append(arg.dtype)
        return arg_defs, call_args, precompile_args, arg_types