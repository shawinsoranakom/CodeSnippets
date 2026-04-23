def def_kernel(
        self,
        inputs: dict[str, ir.Buffer],
        outputs: dict[str, ir.Buffer],
        aliases: dict[str, str] | None = None,
        function_name: str = "",
        extra_sizevars: list[sympy.Expr] | None = None,
        placeholder: str = "<DEF_KERNEL>",
    ) -> str:
        if len(function_name) == 0:
            function_name = str(self.kernel_name)
        for name, inp in inputs.items():
            if inp is not None:
                self.args.input_buffers[inp.get_name()] = name
        for name, out in outputs.items():
            self.args.output_buffers[out.get_name()] = name
        if aliases is not None:
            for alias, orig in aliases.items():
                if orig in self.args.input_buffers:
                    self.args.input_buffers[alias] = self.args.input_buffers[orig]
                if orig in self.args.output_buffers:
                    self.args.output_buffers[alias] = self.args.output_buffers[orig]

        unique_sizevars = OrderedSet(
            s
            for input in inputs.values()
            if input is not None
            for sym in itertools.chain(input.get_size(), input.get_stride())
            if isinstance(sym, sympy.Expr)
            for s in sym.free_symbols
        )
        unique_sizevars.update(
            s
            for sym in extra_sizevars or []
            if isinstance(sym, sympy.Expr)
            for s in sym.free_symbols
        )
        unique_sizevars.update(
            s
            for output in outputs.values()
            for sym in itertools.chain(output.get_size(), output.get_stride())
            if isinstance(sym, sympy.Expr)
            for s in sym.free_symbols
        )
        sizevars = sorted(unique_sizevars, key=str)
        for sizevar in sizevars:
            self.args.sizevars[sizevar] = f"k{sizevar}"

        def hook():
            # remove all aliases before generate function definition
            if aliases is not None:
                for alias in aliases:
                    if alias in self.args.input_buffers:
                        raise AssertionError(
                            f"input_buffers cannot be removed: {alias}"
                        )
                    if alias in self.args.output_buffers:
                        self.args.output_buffers[alias] = REMOVED
            cpp_argdefs, _, _ = self.args.cpp_argdefs()
            return f"void {function_name}({', '.join(cpp_argdefs)})"

        assert placeholder not in self.render_hooks
        self.render_hooks[placeholder] = hook
        return placeholder