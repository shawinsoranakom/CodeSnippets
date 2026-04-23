def codegen_kernel(self, name=None):
        """Called at the end to generate a final kernel string"""
        if self.args.inplace_buffers:
            raise Unsupported("inplace_buffers")
        meta = self.halide_kernel_meta()  # ensure needed args are added early
        code = IndentedBuffer()
        code.splice(
            """
            import halide as hl
            from torch._inductor.runtime import halide_helpers
            from math import inf, nan

            @hl.generator(name="kernel")
            class Kernel:
        """,
            strip=True,
        )
        code.do_indent()
        for _, arg in self.halide_argdefs():
            if isinstance(arg, SizeArg):
                code.writeline(f"{arg.name} = hl.InputScalar({self.index_dtype})")
            else:
                assert arg.buffer, arg
                argcls = "hl.OutputBuffer" if "out" in arg.name else "hl.InputBuffer"
                argtype = halide_type(arg.dtype)
                ndim = len(self.buffer_dimensions[arg.name])
                code.writeline(f"{arg.name} = {argcls}({argtype}, {ndim})")
        code.splice(
            """
            def generate(g):
        """
        )
        code.do_indent()
        for _, arg in self.halide_argdefs():
            code.writeline(f"{arg.name} = g.{arg.name}")
        for old, new in self.args.aliases():
            code.writeline(f"{old} = {new}")
        code.splice(self.indexing_code)

        def update_index(m):
            var = cast(HalideCSEVariable, self.cse.varname_map[m.group(1)])
            assert var.used_dims is not None, var
            return str(var)

        for line in self.body._lines:
            if isinstance(line, str):
                # fill in missing indices
                line = HalideCSEVariable.undefined_re.sub(update_index, line)
            code.writeline(line)
        code.writeline("")
        code.writeline("assert g.using_autoscheduler()")

        for _, arg in self.halide_argdefs():
            # fallback=1 below because halide requires buffers to be at least as large as the estimates
            # This causes crashes if our estimate is greater than the vector length
            # https://github.com/halide/Halide/issues/3103
            if isinstance(arg, SizeArg):
                hint = V.graph.sizevars.optimization_hint(arg.expr, fallback=1)
                code.writeline(f"{arg.name}.set_estimate({hint})")
            else:
                dims = self.buffer_dimensions[arg.name]
                range_hints = []
                for i, dim in enumerate(dims):
                    hint = self._autoscheduler_workarounds(
                        V.graph.sizevars.optimization_hint(dim.size, fallback=1), dims
                    )
                    # pyrefly: ignore [bad-argument-type]
                    range_hints.append(f"hl.Range(0, {hint})")
                    if "out" not in arg.name:
                        code.writeline(f"{arg.name}.dim({i}).set_min(0)")
                        try:
                            code.writeline(
                                f"{arg.name}.dim({i}).set_stride({int(dim.stride)})"
                            )
                        except TypeError:
                            pass  # not integer
                        try:
                            code.writeline(
                                f"{arg.name}.dim({i}).set_extent({int(dim.size)})"
                            )
                        except TypeError:
                            pass  # not integer
                code.writeline(f"{arg.name}.set_estimates([{', '.join(range_hints)}])")

        code.do_unindent(2)
        code.splice(
            """
            if __name__ == "__main__":
                hl.main()
            """.rstrip(),
        )
        if meta.scheduler:
            code.splice(
                f"""
                else:
                    hl.load_plugin({HalideCodeCache.find_libautoschedule(meta.scheduler)!r})
                    target = hl.Target({meta.target!r})
                    autoscheduler = hl.AutoschedulerParams({meta.scheduler!r}, {meta.scheduler_flags!r})
                    with hl.GeneratorContext(target, autoscheduler):
                        gen = Kernel()
                        pipeline = gen._build_pipeline()
                        # gen.compile_to_callable() does not run the autoscheduler
                        pipeline.apply_autoscheduler(target, autoscheduler)
                        kernel = pipeline.compile_to_callable([
                                gen._get_input_parameter(a.name)._to_argument()
                                for a in gen._get_arginfos()
                                if a.dir == hl.ArgInfoDirection.Input
                            ], target)
                """,
                strip=True,
            )
        else:
            code.splice(
                f"""
                  else:
                      with hl.GeneratorContext(hl.Target({meta.target!r})):
                          kernel = Kernel().compile_to_callable()
                  """,
                strip=True,
            )
        return code.getvalue()