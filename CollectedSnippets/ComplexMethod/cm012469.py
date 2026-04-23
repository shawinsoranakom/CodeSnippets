def user_defined_kernel_grid_fn_code(
    name: str,
    configs: list[triton.Config],  # type: ignore[name-defined]
    grids: list[TritonGrid],
    wrapper: PythonWrapperCodegen | None = None,
    original_fxnode_name: str | None = None,
) -> tuple[str, str]:
    output = IndentedBuffer()

    def _convert_to_sympy_expr(item: int | sympy.Expr) -> sympy.Expr:
        return item if isinstance(item, sympy.Expr) else sympy.Integer(item)

    def determine_grid(
        grid: TritonGrid,
        example_grid: TritonGrid | None = None,
    ):
        """
        This function return a tuple of two values: the first one is for the real grid
        which is used in the generated code; the second one is an example grid with
        concreate values which is used in the autotune block to run the generated
        kernels at compile time.
        """
        if wrapper is None or callable(grid):
            # return as-is when used in eager mode or when grid is callable
            return grid, grid
        # Grid contains ints/Expr, so utilize wrapper's expr printer for codegen
        sympy_grid = tuple(_convert_to_sympy_expr(g) for g in grid)
        if not example_grid:
            example_grid = sympy_grid
        return (
            wrapper.codegen_python_shape_tuple(sympy_grid),
            (
                wrapper.codegen_python_shape_tuple(
                    tuple(
                        wrapper.generate_example_arg_value(g, type(g))
                        for g in example_grid  # type: ignore[union-attr]
                    )
                )
                if config.triton.autotune_at_compile_time
                else None
            ),
        )

    def writeline(line: str, example_grid: str | None = None):
        output.writeline(line)
        if (
            wrapper
            and config.triton.autotune_at_compile_time
            and name not in wrapper.kernel_autotune_names
        ):
            wrapper.kernel_autotune_calls.writeline(example_grid or line)

    fn_name = f"grid_wrapper_for_{name}"
    writeline(f"def {fn_name}(meta):")
    kernel_autotune_calls_indent = (
        wrapper.kernel_autotune_calls.indent()
        if wrapper and config.triton.autotune_at_compile_time
        else contextlib.nullcontext()
    )
    with output.indent(), kernel_autotune_calls_indent:
        if (
            config.triton.autotune_at_compile_time
            and original_fxnode_name
            and V.graph.autotuning_grids
            and original_fxnode_name in V.graph.autotuning_grids
        ):
            example_grids = V.graph.autotuning_grids[original_fxnode_name]
        else:
            example_grids = [None] * len(grids)
        if len(grids) == 1:
            grid, example_grid = determine_grid(grids[0], example_grids[0])
            writeline(f"return {grid}", f"return {example_grid}")
        else:
            assert len(grids) > 1
            assert len(grids) == len(configs)
            seen: OrderedSet[str] = OrderedSet()
            # sort the configs from the largest # of kwargs to the smallest to
            # emit the grids in the order of (approximately) decreasing specificity
            # TODO(aakhundov): the sorting below is generally not sufficient, so
            # maybe we'll need to restrict the supported cases to identical kwarg
            # names in all autotuning configs.
            for grid, c, example_grid in sorted(
                zip(grids, configs, example_grids),
                key=lambda x: len(x[1].kwargs),
                reverse=True,
            ):
                guardslist = []
                if c.kwargs:
                    # Remove AMD specific kwargs.
                    for kwarg in c.kwargs:
                        if kwarg not in [
                            "matrix_instr_nonkdim",
                            "waves_per_eu",
                            "kpack",
                        ]:
                            guardslist.append(f"meta['{kwarg}'] == {c.kwargs[kwarg]}")
                if guardslist:
                    guards = " and ".join(guardslist)
                else:
                    guards = "True"  # for configs with empty kwargs
                grid, example_grid = determine_grid(grid, example_grid)
                statement = f"if {guards}: return {grid}"
                if statement in seen:
                    continue
                seen.add(statement)
                writeline(statement, f"if {guards}: return {example_grid}")

    return fn_name, output.getvalue()