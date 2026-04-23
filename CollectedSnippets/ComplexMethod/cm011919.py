def generate_and_load(
        self,
        input_nodes: tuple[ir.IRNode, ...],
        num_stages: int,
        num_warps: int,
        call_sizes: Sequence[sympy.core.symbol.Symbol],
        prefix_args: int,
        suffix_args: int,
        epilogue_fn: Callable[..., Any] | None,
        epilogue_fn_hash: str | None,
        subgraphs: list[ir.Buffer] | None,
        workspace_arg: WorkspaceArg | None,
        num_consumer_groups: int,
        num_buffers_warp_spec: int,
        layout: ir.Layout,
        kwargs: dict[str, Any],
        generate_with_caching,
        hint_override: int | None = None,
        tma_store: bool = False,
        transpose_discontiguous_tensor_descriptors_override: bool | None = None,
        triton_meta: dict[str, Any] | None = None,
    ) -> GenerateAndLoadResult | None:
        """Generate the python code and load it into the current process"""
        caching_enabled = (
            generate_with_caching
            and torch._inductor.config.enable_caching_generated_triton_templates
        )

        cache_key = None
        if caching_enabled:
            cache_key = self._generated_code_cache.make_key(
                input_nodes,
                num_stages,
                num_warps,
                call_sizes,
                prefix_args,
                suffix_args,
                epilogue_fn,
                epilogue_fn_hash,
                tma_store,
                transpose_discontiguous_tensor_descriptors_override,
                subgraphs,
                workspace_arg,
                layout,
                num_consumer_groups,
                num_buffers_warp_spec,
                kwargs,
                hint_override,
                triton_meta,
            )

        assert self.template, "requires jinja2"
        defines = StringIO()

        for name, val in kwargs.items():
            defines.write(f"{name} : tl.constexpr = {val}\n")

        fake_out = ir.Buffer(name="buf_out", layout=layout)
        kernel_name = f"triton_{self.name}"

        numel = sympy_product(layout.size)
        buffers = itertools.chain(input_nodes, (fake_out,))

        if TritonScheduling.can_use_32bit_indexing(numel, buffers):
            index_dtype = "tl.int32"
        else:
            index_dtype = "tl.int64"

        # Add index dtype to defines so it's available in the template
        defines.write(f"INDEX_DTYPE : tl.constexpr = {index_dtype}\n")
        defines = defines.getvalue()

        kernel_options = {
            "input_nodes": input_nodes,
            "defines": defines,
            "num_stages": num_stages,
            "num_warps": num_warps,
            "grid_fn": self.grid,
            "meta": kwargs,
            "call_sizes": call_sizes,
            "prefix_args": prefix_args,
            "suffix_args": suffix_args,
            "epilogue_fn": epilogue_fn,
            "subgraphs": subgraphs,
            "prologue_loads_all_inputs": self.prologue_loads_all_inputs,
            "always_freeze_layout": self.always_freeze_layout,
            "index_dtype_override": index_dtype,
        }

        if HAS_WARP_SPEC:
            kernel_options.update(
                {
                    "num_consumer_groups": num_consumer_groups,
                    "num_buffers_warp_spec": num_buffers_warp_spec,
                }
            )

        def make_kernel():
            return self.kernel_type(
                kernel_name=kernel_name,
                output_node=fake_out,
                workspace_arg=workspace_arg,
                use_jit=False,
                hint_override=hint_override,
                tma_store=tma_store,
                transpose_discontiguous_tensor_descriptors_override=transpose_discontiguous_tensor_descriptors_override,
                triton_meta=triton_meta,
                **kernel_options,
            )

        def generate_code(kernel) -> tuple[str, str] | None:
            def make_extra() -> str:
                extra_parts = [
                    f"{kwarg}={repr(kwargs[kwarg])}" for kwarg in sorted(kwargs.keys())
                ]

                extra_parts.extend(
                    [
                        f"num_stages={num_stages}",
                        f"num_warps={num_warps}",
                    ]
                )
                if HAS_WARP_SPEC:
                    extra_parts.extend(
                        [
                            f"num_consumer_groups={num_consumer_groups}",
                            f"num_buffers_warp_spec={num_buffers_warp_spec}",
                        ]
                    )
                extra = "-".join(extra_parts) + "-"
                return extra

            try:
                template = kernel.render(self.template, kwargs, caching_enabled)
                code = template.finalize_all()
            except ZeroDivisionError:
                # TODO(nmacchioni): fix sympy division by zero
                return None
            if self.debug:
                print("Generated Code:\n", code)

            extra = make_extra()
            return code, extra

        def maybe_test_cache(code: str, extra: str, kernel):
            if self.test_cache or self.debug:
                with (
                    patch.object(V.graph, "get_dtype", self._fake_get_dtype(fake_out)),
                    V.graph.set_current_device(layout.device),
                    make_kernel() as kernel_test,
                ):
                    result2 = generate_code(kernel_test)
                    assert result2 is not None
                    code_test, extra_test = result2
                    assert (
                        code == code_test
                        and extra == extra_test
                        and kernel.args.input_buffers == kernel_test.args.input_buffers
                        and kernel.prologue_supported_inputs
                        == kernel_test.prologue_supported_inputs
                        and kernel.args.sizevars == kernel_test.args.sizevars
                    ), "Generated code cache results in wrong output"

        # Generate code, extra.
        code: str | None = None
        extra: str | None = None
        with (
            patch.object(V.graph, "get_dtype", self._fake_get_dtype(fake_out)),
            V.graph.set_current_device(layout.device),
            make_kernel() as kernel,
        ):
            cache_entry = self._generated_code_cache.get_entry(cache_key)
            cache_hit = False

            if cache_entry is not None:
                code, extra, events = cache_entry
                kernel.replay_cached_events(events)
                cache_hit = True

            else:
                result = generate_code(kernel)
                if result is None:  # happens at ZeroDivisionError:
                    return None
                code, extra = result
                self._generated_code_cache.put_entry(
                    cache_key, code, extra, kernel.cached_replay_events
                )

        assert code is not None and extra is not None

        mod = PyCodeCache.load(code, extra)

        input_call_args = tuple(kernel.args.input_buffers.keys())
        prologue_supported_inputs = kernel.prologue_supported_inputs.copy()
        kernel_args_sizevars_keys = tuple(kernel.args.sizevars.keys())

        if cache_hit:
            maybe_test_cache(code, extra, kernel)

        return GenerateAndLoadResult(
            mod,
            extra,
            input_call_args,
            prologue_supported_inputs,
            kernel_args_sizevars_keys,
            kernel_options,
        )