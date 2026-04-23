def generate_code_and_args(
        self, name: str, input_key: str, layout_repr: str, **kwargs
    ) -> tuple[str, tuple[int, ...]]:
        """
        Generate code and args with caching. We cache the code even if runtime
        args are different.
        """
        key: str | None = None
        if config.cutlass.enable_caching_codegen:
            key = self.make_key(name=name, input_key=input_key, layout_repr=layout_repr)

        if key is not None and key in self.code_cache:
            code, size_args, offset_args = self.code_cache[key]
            extra_args = tuple(
                list(size_args)
                + list(offset_args)
                + list(self.get_runtime_arg_values(**kwargs))
            )
            return code, extra_args

        kernel_name = str(Placeholder.KERNEL_NAME)
        kernel = CUTLASSTemplateKernel(
            kernel_name=kernel_name,
            runtime_arg_info=self.get_runtime_arg_info(),
            runtime_arg_values=self.get_runtime_arg_values(**kwargs),
            device_type=self.device_type,
        )
        with patch.object(V.graph, "get_dtype", self._fake_get_dtype(self.output_node)):
            code = self.render(kernel=kernel, **kwargs)
            _, call_args, _, _ = kernel.args.python_argdefs()
            autotuning_log.debug("Generated Code:\n%s", code)
            autotuning_log.debug(
                "Args: cpp_argdefs: %s, python_argdefs: %s",
                kernel.args.cpp_argdefs(DTYPE_TO_CUTLASS_TYPE),
                kernel.args.python_argdefs(),
            )

        input_reorder = (
            self.input_reorder
            if self.input_reorder is not None
            else list(range(len(self.input_nodes)))
        )
        expected_args = list(
            unique(self.input_nodes[idx].get_name() for idx in input_reorder)
        )
        expected_args.extend([self.output_node.get_name()])
        assert list(call_args)[: len(expected_args)] == expected_args, (
            call_args,
            expected_args,
        )
        # Resolve symbolic sizes to concrete ints for benchmarking only.
        V.graph.sizevars.optimization_hints(
            map(sympy.expand, call_args[len(expected_args) :])
        )
        size_args = V.graph.sizevars.optimization_hints(kernel.get_dynamic_shape_args())
        offset_args = V.graph.sizevars.optimization_hints(kernel.get_offset_args())

        if key is not None:
            self.code_cache[key] = code, size_args, offset_args

        # extra args has runtime params, which shouldn't be cached
        extra_args = tuple(
            list(size_args) + list(offset_args) + self.get_runtime_arg_values(**kwargs)
        )

        return code, extra_args