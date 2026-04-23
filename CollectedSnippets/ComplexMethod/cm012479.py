def define_user_defined_triton_kernel(
        self,
        kernel,
        configs,
        kwargs,
        restore_value_args,
        reset_to_zero_args,
        grids: list[list[int | sympy.Expr]],
        epilogue_fusion: tuple[ir.ComputedBuffer, str] | None,
    ):
        from ..runtime.triton_heuristics import (
            config_to_dict,
            FixedGrid,
            PrecomputedGrid,
        )
        from .common import (
            ConstexprArg,
            KernelArgType,
            SizeArg,
            TensorArg,
            TMADescriptorArg,
        )

        original_name = kernel.__name__
        signature: list[KernelArgType] = []
        constants: dict[str, Any] = {}
        arg_indices: list[int] = []
        equal_to_1_args: list[str] = []

        def add_to_signature(idx, arg):
            signature.append(arg)
            arg_indices.append(idx)

        def add_arg(idx, arg, is_constexpr=False, equals_1=False, equals_none=False):
            if is_constexpr:
                if triton_version_uses_attrs_dict():
                    # tl.constexpr args appear in the signature in new versions of triton,
                    # but not in old versions of triton.
                    add_to_signature(idx, arg)

                if arg.name in kwargs:
                    # the arg may not appear in kwargs if it is an autotuned arg.
                    # in this case, it will be added in triton_heuristics after autotuning.
                    constants[arg.name] = kwargs[arg.name]

            else:
                # the only case where arg name isn't in kwargs, should be
                # when the arg is a constexpr.
                assert arg.name in kwargs

                if equals_1:
                    if triton_version_uses_attrs_dict():
                        # new versions of triton: add the equal-to-1 arg in the signature (labeled as "constexpr"),
                        #                         and add the arg as a constant.
                        # new versions of triton: add the equal-to-1 arg in the signature (labeled as, e.g., "i32"),
                        #                         and add the arg as a constant.
                        add_to_signature(idx, ConstexprArg(name=arg.name))
                    else:
                        add_to_signature(idx, arg)
                    constants[arg.name] = 1
                elif equals_none:
                    if triton_version_uses_attrs_dict():
                        # new versions of triton: add the none arg in the signature (as a constexpr arg) and as a constant
                        # old versions of triton: include the none arg as a constant (but not in the signature)
                        add_to_signature(idx, ConstexprArg(name=arg.name))
                    constants[arg.name] = None
                else:
                    add_to_signature(idx, arg)

        arg_names = [p.name for p in kernel.params]
        constexprs = [p.num for p in kernel.params if p.is_constexpr]
        for idx, key in enumerate(arg_names):
            if idx in constexprs:
                add_arg(idx, ConstexprArg(name=key), is_constexpr=True)
                continue

            if key not in kwargs:
                continue

            arg = kwargs[key]

            if kwargs[key] is None:
                add_arg(idx, ConstexprArg(name=key), equals_none=True)
            else:
                if isinstance(arg, ir.TMADescriptor):
                    api_type, block_shape, dtype = (
                        ("stable", arg.block_shape, arg.tensor.get_dtype())
                        if isinstance(arg, ir.TMADescriptorStable)
                        else ("experimental", None, None)
                    )
                    add_arg(
                        idx,
                        TMADescriptorArg(
                            name=key,
                            api_type=api_type,
                            block_shape=block_shape,
                            dtype=dtype,
                        ),
                    )
                elif isinstance(arg, ir.Buffer):
                    add_arg(
                        idx,
                        TensorArg(
                            name=key,
                            buffer=arg.get_name(),
                            dtype=arg.get_dtype(),
                        ),
                    )
                elif isinstance(arg, ir.ReinterpretView):
                    # for ReinterpretView we use the underlying
                    # buffer name and note the (possibly non-zero)
                    # offset relative to the underlying buffer
                    add_arg(
                        idx,
                        TensorArg(
                            name=key,
                            buffer=arg.data.get_name(),
                            dtype=arg.get_dtype(),
                            offset=arg.layout.offset,
                        ),
                    )
                else:
                    equals_1 = isinstance(
                        arg, (int, sympy.Integer)
                    ) and V.graph.sizevars.statically_known_equals(
                        arg,
                        1,  # type: ignore[arg-type]
                    )
                    add_arg(idx, SizeArg(key, arg), equals_1=equals_1)

        triton_signature = signature_to_meta(
            signature,
            size_dtype=None,  # try to infer based on symints
            indices=arg_indices,
            argdefs=[ArgName(x) for x in kernel.arg_names],
        )
        triton_meta: dict[str, Any] = {
            "signature": triton_signature,
            "device": DeviceProperties.create(V.graph.get_current_device_or_throw()),
            # Triton compiler includes equal_to_1 args into constants even
            # when they are not constexpr. otherwise there may be a segfault
            # during launching the Inductor-compiled Triton kernel.
            # TODO(aakhundov): add None args to constants, too. currently, this
            # causes CUDA errors in test_aot_inductor.test_triton_kernel_with_none_input.
            # https://github.com/pytorch/pytorch/issues/120478#issuecomment-1962822307
            # https://github.com/triton-lang/triton/blob/231efe9ed2d200be0f69a07c298e4342b08efe3d/python/triton/runtime/jit.py#L384
            "constants": {
                **constants,
                **dict.fromkeys(equal_to_1_args, 1),
            },
            "configs": [
                config_of(
                    signature,
                    indices=arg_indices,
                )
            ],
        }

        if restore_value_args:
            triton_meta["restore_value"] = tuple(restore_value_args)

        if reset_to_zero_args:
            triton_meta["reset_to_zero"] = tuple(reset_to_zero_args)

        if len(grids) == 1:
            # compute the grid in the wrapper and pass it in as an arg
            inductor_meta: dict[str, Any] = FixedGrid.setup_grid_as_args()
            extra_launcher_call_args = [*map(sympy.sympify, grids[0])]
        else:

            def rename_sizes_for_launcher(expr: int | sympy.Expr) -> sympy.Expr:
                if isinstance(expr, sympy.Expr):
                    symbols = [*expr.free_symbols]
                    if not symbols:
                        return expr
                    symbols.sort(key=str)
                    for sym in symbols:
                        if sym in extra_launcher_args:
                            continue
                        extra_launcher_args[sym] = sympy.Symbol(
                            f"_launcher_s{len(extra_launcher_args)}"
                        )
                    return sympy_subs(expr, extra_launcher_args)
                assert isinstance(expr, int)
                return sympy.Integer(expr)

            extra_launcher_args: dict[sympy.Symbol, sympy.Symbol] = {}
            grids = [[*map(rename_sizes_for_launcher, grid)] for grid in grids]

            assert grids and len(grids) == len(configs)
            precomputed_grids = []
            for grid, cfg in sorted(
                zip(grids, configs), key=lambda x: len(x[1].kwargs), reverse=True
            ):
                precomputed_grids.append(
                    {
                        "config": config_to_dict(cfg),
                        "python": [*map(pexpr, grid)],
                        "cpp": [*map(cexpr, grid)],
                        "python_slow": [*map(pexpr, grid)],
                    }
                )
            inductor_meta = {
                "grid_type": PrecomputedGrid.__name__,
                "precomputed_grids": precomputed_grids,
                "extra_launcher_args": [*map(str, extra_launcher_args.values())],
            }
            extra_launcher_call_args = [*extra_launcher_args.keys()]

        if constexprs:
            inductor_meta["declared_constexpr_names"] = [
                arg_names[i] for i in constexprs
            ]

        # Distinguish between different functions using function id
        cache_key: Any = [id(kernel.fn)]
        if len(configs) > 0:
            for arg in kwargs.values():
                # We need to key on non tensor arg only in autotune mode
                if not isinstance(arg, (ir.Buffer, ir.ReinterpretView)):
                    cache_key.append(arg)
        cache_key.append(str(triton_meta))
        cache_key.extend(str(inductor_meta))

        if epilogue_fusion is not None:
            cache_key.append((epilogue_fusion[0].get_name(), epilogue_fusion[1]))

        cache_key = tuple(cache_key)
        if cache_key in self.user_defined_kernel_cache:
            name, triton_meta, cached_inductor_meta = self.user_defined_kernel_cache[
                cache_key
            ]
            return (
                name,
                triton_meta,
                cached_inductor_meta,
                extra_launcher_call_args,
            )

        name = f"{original_name}_{len(self.user_defined_kernel_cache)}"

        compile_wrapper = IndentedBuffer()
        if config.triton.unique_user_kernel_names:
            compile_wrapper.writeline(f"async_compile.triton({name!r}, '''")
        else:
            compile_wrapper.writeline(f"async_compile.triton({original_name!r}, '''")

        inductor_meta["kernel_name"] = name
        triton_info_kernel_cls = self._get_triton_info_kernel_cls()
        inductor_meta.update(triton_info_kernel_cls.inductor_meta_common())

        compile_wrapper.splice(triton_info_kernel_cls.gen_common_triton_imports())
        if config.triton.proton_profiling:
            compile_wrapper.writeline('pl.enable_semantic("triton")')

        compile_wrapper.splice(
            f"""
            @triton_heuristics.user_autotune(
                configs={[*map(config_to_dict, configs)]!r},
                inductor_meta={inductor_meta!r},
                triton_meta={triton_meta!r},
                filename=__file__,
                custom_kernel=True,
            )
            @triton.jit
            """
        )
        kernel_src = user_defined_triton_kernel_transitive_closure_source_code(
            kernel, epilogue_fusion
        )
        if config.triton.unique_user_kernel_names:
            # We replace the original_name with the unique name.
            kernel_src = kernel_src.replace(f"def {original_name}(", f"def {name}(")
        if config.cpp_wrapper:
            # With cpp_wrapper + autotune_at_compile_time=False, the source is
            # further embedded in a C++ raw string inside a Python r"""...""" wrapper.
            # So we need to add backslash here.
            kernel_src = kernel_src.replace('"""', '\\"\\"\\"')
        kernel_src = kernel_src.replace("'''", "\\'\\'\\'")
        compile_wrapper.splice(kernel_src)

        current_device = V.graph.get_current_device_or_throw()
        compile_wrapper.writeline(f"''', device_str='{current_device.type}')")
        _, lineno = inspect.getsourcelines(kernel.fn)
        srcfile = inspect.getsourcefile(kernel.fn)
        metadata = f"# Original path: {srcfile}:{lineno}"
        self.define_kernel(
            name,
            compile_wrapper.getvalue(),
            metadata,
        )
        # Add to the cache for the next use
        self.user_defined_kernel_cache[cache_key] = (name, triton_meta, inductor_meta)
        return name, triton_meta, inductor_meta, extra_launcher_call_args