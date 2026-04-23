def call_kernel(
        self, name: str, node: Any = None, deallocate_ws: bool = True
    ) -> None:
        """
        Codegens a call to this kernel
        """
        wrapper = V.graph.wrapper_code
        # Make sure sizevars has been computed
        for v in self.args.sizevars:
            wrapper.ensure_size_computed(v)

        _, call_args, _, arg_types = self.args.python_argdefs()
        arg_name_to_type = {
            str(call_arg): arg_type for call_arg, arg_type in zip(call_args, arg_types)
        }

        args = [*self.args.output_buffers.keys(), *self.args.input_buffers.keys()]
        args = [arg for arg in args if arg not in self.removed_buffers]
        args += [str(v) for v in self.args.sizevars]
        arg_types = [arg_name_to_type[arg] for arg in args]

        # Add any dynamic ints as inputs
        for tree in self.range_trees:
            if isinstance(tree.numel, (sympy.Integer, int)):
                # Don't need to pass in integers as inputs
                continue
            elif isinstance(tree.numel, sympy.Symbol):
                expr = tree.numel
            else:
                expr = V.graph.wrapper_code.generate_numel_expr(name, tree).inner

            if not tree.is_reduction or self.inside_reduction:
                args.append(str(expr))
                arg_types.append(int)

        expr_printer = self.cexpr if V.graph.cpp_wrapper else self.pexpr

        def format_threads(threads: list[str], kwarg: str) -> str:
            if V.graph.cpp_wrapper:
                threads = [f"static_cast<uint64_t>({t})" for t in threads]
                return f"{{{', '.join(threads)}}}"
            else:
                return f"{kwarg}=[{', '.join(threads)}]"

        # For reduction kernels, limit the maximum size over reduction dimensions to
        # a maximum threadgroup size
        if len(self.active_range_trees()) > 0:
            threads = [
                expr_printer(
                    sympy.Min(v.numel, self.max_threadgroup_size)  # type: ignore[misc]
                    if v.is_reduction
                    else v.numel
                )
                for v in self.active_range_trees()
            ]

            args.append(format_threads(threads, "threads"))
            arg_types.append(list)
        else:
            if V.graph.cpp_wrapper:
                raise RuntimeError("We should always have threads?")

        if self.inside_reduction:
            threads = [
                expr_printer(sympy.Min(v.numel, self.max_threadgroup_size))  # type: ignore[misc]
                if v.is_reduction
                else "1"
                for v in self.active_range_trees()
            ]
            args.append(format_threads(threads, "group_size"))
            arg_types.append(list)
        else:
            if V.graph.cpp_wrapper:
                # Add a None so that we always have a group_size in the
                # arguments. We won't use it if the value is None.
                args += [None]  # type: ignore[list-item]
                arg_types.append(None)

        # Add error buffer index if error reporting is used
        # TODO(malfet) Figure out how to do it for aoti
        if "error" in self.headers and not V.graph.cpp_wrapper:
            args.append(
                f"error_buf_idx={len([arg for arg in args if arg is not None and '=' not in arg])}"
            )

        wrapper.generate_kernel_call(
            name,
            args,
            device=torch.device("mps"),
            triton=False,
            arg_types=arg_types,
        )