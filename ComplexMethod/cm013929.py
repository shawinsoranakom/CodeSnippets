def SHAPE_ENV(self, guard: Guard) -> None:
        from torch._dynamo.output_graph import OutputGraphCommon

        assert guard.name == ""
        output_graph = self.check_fn_manager.output_graph
        assert output_graph is not None
        if self.check_fn_manager.shape_code_parts is not None:
            shape_code_parts = self.check_fn_manager.shape_code_parts
            python_code_parts = shape_code_parts.python_code_parts
            verbose_code_parts = shape_code_parts.verbose_code_parts
            if shape_code_parts.cpp_code_parts is not None:
                cpp_code_parts = shape_code_parts.cpp_code_parts
            python_fallback = shape_code_parts.python_fallback
        else:
            # Let's handle ShapeEnv guards.  To do this, we will resolve
            # shape variables to sources from tracked_fakes.  This must happen after
            # tensor checks.
            # NB: self.output_graph can be None in the debug_nops tests
            assert isinstance(output_graph, OutputGraphCommon)
            assert output_graph.shape_env is not None
            fs = output_graph.shape_env.tracked_fakes or []
            input_contexts = [a.symbolic_context for a in fs]

            def get_sources(t_id: int, dim: int) -> list[Source]:
                # Looks up base sources mapped to a tensor id and uses them to create
                # sources for the corresponding tensor dimension.
                return [
                    TensorPropertySource(source, TensorProperty.SIZE, dim)
                    # pyrefly: ignore [missing-attribute]
                    for source in output_graph.tracked_fakes_id_to_source[t_id]
                ]

            if output_graph.export_constraints:
                names: dict[str, tuple[int, int]] = {}
                source_pairs: list[tuple[Source, Source]] = []
                derived_equalities: list[  # type: ignore[type-arg]
                    # pyrefly: ignore [implicit-any]
                    tuple[Source, Source | Symbol, Callable]
                ] = []
                phantom_symbols: dict[str, Symbol] = {}
                relaxed_sources: set[Source] = set()
                for constraint in output_graph.export_constraints:  # type: ignore[attr-defined]
                    if constraint.t_id in output_graph.tracked_fakes_id_to_source:
                        torch.export.dynamic_shapes._process_equalities(
                            constraint,
                            get_sources,
                            output_graph.shape_env,
                            names,
                            source_pairs,
                            derived_equalities,
                            phantom_symbols,
                            relaxed_sources,
                        )
                    else:
                        log.warning("Untracked tensor used in export constraints")
                equalities_inputs = EqualityConstraint(
                    source_pairs=source_pairs,
                    derived_equalities=derived_equalities,
                    phantom_symbols=list(phantom_symbols.values()),
                    relaxed_sources=relaxed_sources,
                    warn_only=False,
                )
            else:
                equalities_inputs = None

            def _get_code_parts(langs: tuple[str, ...]) -> list[_ShapeGuardsHelper]:
                # pyrefly: ignore [missing-attribute]
                return output_graph.shape_env.produce_guards_verbose(
                    [a.fake for a in fs],  # type: ignore[misc]
                    [a.source for a in fs],
                    input_contexts=input_contexts,  # type: ignore[arg-type]
                    equalities_inputs=equalities_inputs,
                    source_ref=self.source_ref,
                    # Export keeps static.
                    # pyrefly: ignore [missing-attribute]
                    ignore_static=(not output_graph.export),
                    langs=langs,
                )

            if config.enable_cpp_symbolic_shape_guards:
                try:
                    # For exporting we need the python code parts
                    python_code_parts, verbose_code_parts, cpp_code_parts = (
                        _get_code_parts(("python", "verbose_python", "cpp"))  # type: ignore[assignment]
                    )
                    python_fallback = False
                except OverflowError:
                    # Cannot use int64_t
                    python_fallback = True
                    python_code_parts, verbose_code_parts = _get_code_parts(
                        ("python", "verbose_python")
                    )
            else:
                python_fallback = True
                python_code_parts, verbose_code_parts = _get_code_parts(
                    ("python", "verbose_python")
                )

            # When exporting, we may work with the shape constraints some more in
            # postprocessing, so don't freeze yet
            if not output_graph.export:
                output_graph.shape_env.freeze()

        if self.save_guards:
            # For SHAPE_ENV we want to skip serializing the entire ShapeEnv so instead
            # we directly serialize the generated code here.
            maybe_cpp_code_parts = locals().get("cpp_code_parts")
            assert maybe_cpp_code_parts is None or isinstance(
                maybe_cpp_code_parts, _CppShapeGuardsHelper
            )
            maybe_shape_env_sources = (
                []
                if maybe_cpp_code_parts is None
                else list(maybe_cpp_code_parts.source_to_symbol.keys())
            )
            self.check_fn_manager.shape_code_parts = ShapeCodeParts(
                python_code_parts=python_code_parts,
                verbose_code_parts=verbose_code_parts,
                cpp_code_parts=maybe_cpp_code_parts,
                python_fallback=python_fallback,
                shape_env_sources=maybe_shape_env_sources,
            )

        for code in python_code_parts.exprs:
            self._set_guard_export_info(guard, [code])

        # Make ShapeEnv guards available for testing.
        if compile_context := CompileContext.try_get():
            compile_context.shape_env_guards.extend(verbose_code_parts.exprs)

        int_source_to_symbol = []
        float_source_to_symbol = []

        if not python_fallback:
            assert cpp_code_parts  # type: ignore[possibly-undefined]
            code_parts, source_to_symbol = (
                # pyrefly: ignore [unbound-name]
                cpp_code_parts.exprs,
                # pyrefly: ignore [unbound-name, missing-attribute]
                cpp_code_parts.source_to_symbol,
            )

            if not code_parts:
                return

            for source, symbol in source_to_symbol.items():
                if isinstance(source, ConstantSource):
                    python_fallback = True
                else:
                    example_value = self.get(
                        source,
                        closure_vars={**SYMPY_INTERP, **_get_closure_vars()},
                    )
                    if isinstance(example_value, int):
                        int_source_to_symbol.append((source, symbol))
                    elif isinstance(example_value, float):
                        float_source_to_symbol.append((source, symbol))
                    else:
                        # SymInts/SymFloats go through python guard as we only support
                        # int64_t/double in C++ guards for now.
                        python_fallback = True

        if not python_fallback:
            import ctypes

            from torch._inductor.codecache import CppCodeCache

            assert cpp_code_parts  # type: ignore[possibly-undefined]
            code_parts, source_to_symbol = (
                # pyrefly: ignore [unbound-name]
                cpp_code_parts.exprs,
                # pyrefly: ignore [unbound-name, missing-attribute]
                cpp_code_parts.source_to_symbol,
            )

            source_to_symbol = dict(int_source_to_symbol + float_source_to_symbol)
            try:
                guard_managers = [
                    self.get_guard_manager_from_source(IndexedSource(source, i))
                    for i, source in enumerate(source_to_symbol)
                ]

                int_symbols_str = ", ".join(
                    f"{symbol} = int_values[{i}]"
                    for i, (_, symbol) in enumerate(int_source_to_symbol)
                )
                float_symbols_str = ", ".join(
                    f"{symbol} = float_values[{i}]"
                    for i, (_, symbol) in enumerate(float_source_to_symbol)
                )

                if int_symbols_str:
                    int_symbols_str = f"int64_t {int_symbols_str};"
                if float_symbols_str:
                    float_symbols_str = f"double {float_symbols_str};"

                func_str = textwrap.dedent(
                    f"""
                #include <algorithm>
                #include <cstdint>
                #include <cmath>
                #include <c10/util/generic_math.h>

                #if defined(_MSC_VER)
                #  define EXTERN_DLL_EXPORT extern "C" __declspec(dllexport)
                #else
                #  define EXTERN_DLL_EXPORT extern "C"
                #endif

                EXTERN_DLL_EXPORT int8_t guard(int64_t *int_values, double *float_values) {{
                  {int_symbols_str}
                  {float_symbols_str}
                  return ({") && (".join(code_parts)});
                }}
                """
                )
                guards_log.debug(
                    "C++ shape guard function: %s %s",
                    func_str,
                    verbose_code_parts.exprs,
                )
                clib = CppCodeCache.load(func_str)
                cguard = ctypes.cast(clib.guard, ctypes.c_void_p).value
                assert cguard
            except torch._inductor.exc.InvalidCxxCompiler:
                # No valid C++ compiler to compile the shape guard
                pass
            else:
                install_symbolic_shape_guard(
                    guard_managers,
                    len(int_source_to_symbol),
                    len(float_source_to_symbol),
                    cguard,
                    clib,
                    verbose_code_parts.exprs,
                    guard.user_stack,
                )
                return

        # Install all the symbolic guards in one python lambda guard. These are run
        # at the very end of the RootGuardManager via epilogue guards.
        # TODO(anijain2305,williamwen42) - Consider moving this to C++.
        if python_code_parts.exprs:
            self.add_python_lambda_leaf_guard_to_root(
                python_code_parts.exprs,
                verbose_code_parts.exprs,
                closure_vars={**SYMPY_INTERP, **_get_closure_vars()},
            )