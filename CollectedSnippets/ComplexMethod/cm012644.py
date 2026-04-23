def _generate_triton_call(self, line: WrapperLine) -> None:
        assert isinstance(line, KernelCallLine)

        # Collect all kwargs, including autotuned block sizes.
        call_args = self._lookup_args(line.call_args)
        kernel = self.kernels[line.kernel_name]
        tuner = kernel.tuner

        def tune_kernel(tuner: CachingAutotuner, call_args: Sequence[Any]) -> None:
            from triton.runtime import driver

            log.info("Autotuning Triton kernel %s at compile time.", kernel_name)

            device = driver.active.get_current_device()

            stream = driver.active.get_current_stream(device)

            def node_to_tuning_arg(arg: Any) -> Any:
                """
                Create real tensors for autotuning arguments, substituting size hints
                for dynamic shapes.
                """

                def to_size_hint_sympy_int(arg: sympy.Expr | int) -> int:
                    return V.graph.sizevars.optimization_hint(arg)

                def to_size_hint_list(arg: list[torch.SymInt | int]) -> list[int]:
                    args_sympy = [
                        x.node.expr if isinstance(x, torch.SymInt) else x for x in arg
                    ]
                    return pytree.tree_map(to_size_hint_sympy_int, args_sympy)

                if not isinstance(arg, torch.fx.Node):
                    return to_size_hint_sympy_int(arg)

                fake = arg.meta["val"]
                return torch.empty_strided(
                    to_size_hint_list(fake.shape),
                    to_size_hint_list(fake.stride()),
                    dtype=fake.dtype,
                    device=device,
                ).zero_()

            # call args can be fx nodes or sympy expressions or integers!
            arg_values = [node_to_tuning_arg(arg) for arg in call_args]
            tuner.run(*arg_values, stream=stream)

        # Optionally autotune the kernels.
        # The FX backend currently only supports compile-time tuning.
        kernel_name = tuner.fn.__name__
        if config.triton.autotune_at_compile_time:
            # Skip compile-time autotuning if any unbacked symbol lacks a user-provided
            # optimization hint — autotuning with the generic fallback would
            # produce meaningless results.
            hinted = V.graph.sizevars.all_unbacked_explicitly_hinted
            can_tune = True
            for arg in call_args:
                if isinstance(arg, torch.fx.Node):
                    fake = arg.meta["val"]
                    if not hinted(list(fake.shape) + list(fake.stride())):
                        can_tune = False
                        break
                elif not hinted(arg):
                    can_tune = False
                    break
            if can_tune:
                tune_kernel(tuner, call_args)
            else:
                log.info(
                    "Detected unhinted unbacked symints. Skipping compile-time autotuning for kernel %s.",
                    kernel_name,
                )
        else:
            log.info(
                "Skipping autotuning for kernel %s. Set config.triton.autotune_at_compile_time = True to enable.",
                kernel_name,
            )

        triton_meta = tuner.triton_meta
        signature = triton_meta["signature"]

        def add_constants_to_call_args(
            call_args: Sequence[Any], cfg: Config
        ) -> tuple[Any, ...]:
            """
            Add constant kwargs to the arg list.
            """
            # Add args from the proper Triton signature.
            # Exclude constants and config kwargs, as those are tracked separately.
            new_call_args = []
            constants = triton_meta["constants"]
            call_kwargs = {
                key: val
                for key, val in zip(signature, call_args)
                # pyrefly: ignore [missing-attribute]
                if key not in constants and key not in cfg.kwargs
            }

            # Add constants stored as Triton metadata, in signature order.
            call_kwargs |= constants
            new_call_args = [
                call_kwargs[key]
                for key in signature
                # pyrefly: ignore [missing-attribute]
                if key not in cfg.kwargs
            ]

            # Add Inductor's extra launcher args to the end.
            if extra_launcher_args := tuner.inductor_meta.get("extra_launcher_args"):
                new_call_args.extend(
                    call_args[len(call_args) - len(extra_launcher_args) :]
                )

            return tuple(new_call_args)

        kernel_config = tuner.compile_results[0].config
        extra_options = getattr(kernel_config, "extra_options", None)
        call_args = add_constants_to_call_args(call_args, kernel_config)
        call_args, grid = tuner._interpret_args_grid(call_args, kernel_config)
        call_kwargs = dict(zip(signature, call_args))
        # pyrefly: ignore [missing-attribute]
        assert not any(kwarg in kernel_config.kwargs for kwarg in call_kwargs), (
            f"kwargs overlap config: {call_kwargs}"
        )
        # pyrefly: ignore [missing-attribute]
        call_kwargs.update(kernel_config.kwargs)

        # Replace sympy.floor with FloorDiv, to make the expression traceable.
        grid = [replace_floor_div(x) if isinstance(x, sympy.Expr) else x for x in grid]
        wrapper_grid = [tuple(self._generate_sym_nodes(grid))]
        call_kwargs = {
            name: self._generate_sym_node(val) for name, val in call_kwargs.items()
        }

        # Store non-graphable kwargs in the side table.
        (
            call_kwargs,
            constant_args_idx,
        ) = tracing_triton_hopifier_singleton.store_non_graphable_args(call_kwargs)

        triton_node = self.gm.graph.call_function(
            triton_kernel_wrapper_mutation,
            kwargs={
                "kernel_idx": kernel.wrapped.kernel_idx,
                "constant_args_idx": constant_args_idx,
                "grid": wrapper_grid,
                "tma_descriptor_metadata": {},
                "kwargs": call_kwargs,
            },
        )
        if extra_options:
            triton_node.meta["extra_options"] = extra_options