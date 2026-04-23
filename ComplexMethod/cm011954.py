def fx_codegen_and_compile(
    gm: GraphModule,
    example_inputs: Sequence[InputType],
    # This is derivable from the other inputs to this function, but we pass it
    # in explicitly because it's nontrivial to compute
    inputs_to_check: Sequence[int],
    compile_region_name: str | None = None,
    **graph_kwargs: Unpack[_CompileFxKwargs],
) -> OutputCode:
    scheme: FxCompile

    if fx_compile_mode == FxCompileMode.NORMAL:
        scheme = _InProcessFxCompile()
    elif fx_compile_mode == FxCompileMode.SERIALIZE:
        from .compile_fx_ext import _DebugSerdeFxCompile

        scheme = _DebugSerdeFxCompile()
    elif fx_compile_mode == FxCompileMode.SUBPROCESS:
        from .compile_fx_subproc import _SubprocessFxCompile

        scheme = _SubprocessFxCompile()

    if fx_compile_async:
        from .compile_fx_async import _AsyncFxCompile
        from .compile_fx_ext import _OutOfProcessFxCompile

        # pyrefly: ignore [unbound-name]
        assert isinstance(scheme, _OutOfProcessFxCompile), (
            "async is only valid with an out-of-process compile mode"
        )
        # pyrefly: ignore [unbound-name]
        scheme = _AsyncFxCompile(scheme)
        scheme._compile.compile_region_name = (
            compile_region_name  # pyrefly: ignore[attr-defined]
        )

    if fx_compile_progressive:
        from .compile_fx_async import _ProgressiveFxCompile
        from .compile_fx_ext import _OutOfProcessFxCompile

        # pyrefly: ignore [unbound-name]
        assert isinstance(scheme, _OutOfProcessFxCompile), (
            "progressive is only valid with an out-of-process compile mode"
        )

        progression_configs = _get_progression_configs()

        # Use in-process compile for the fast version
        fast_scheme = _InProcessFxCompile()
        fast_scheme.compile_region_name = compile_region_name

        # pyrefly: ignore [unbound-name]
        scheme = _ProgressiveFxCompile(fast_scheme, scheme, progression_configs)
        scheme._optimized_compile.compile_region_name = (
            compile_region_name  # pyrefly: ignore[attr-defined]
        )

    scheme.compile_region_name = compile_region_name  # pyrefly: ignore[unbound-name]

    # pyrefly: ignore [unbound-name]
    return scheme.codegen_and_compile(gm, example_inputs, inputs_to_check, graph_kwargs)