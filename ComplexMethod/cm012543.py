def generate_custom_op_choices(
        self,
        name: str,
        decompositions: list[Callable[..., Any]],
        input_nodes: list[Buffer],
        non_tensor_args: list[dict[str, Any]],
        default_impl: Callable[..., Any] | None = None,
        input_gen_fns: dict[int, Callable[[Any], torch.Tensor]] | None = None,
        config_patches_list: list[dict[str, Any]] | None = None,
    ) -> list[SubgraphChoiceCaller]:
        """
        Generate multiple SubgraphChoiceCaller instances for custom op autotuning.

        This method extends SubgraphTemplate to support custom op decompositions,
        allowing multiple implementations to compete in autotuning.

        Args:
            name: Base name for the choices
            decompositions: List of decomposition functions to compete in autotuning
            input_nodes: List of tensor inputs. All tensor arguments must be passed here.
            non_tensor_args: List of non-tensor kwargs only, one dict per corresponding decomposition.
            default_impl: Default implementation for layout inference
            input_gen_fns: Optional dict mapping input indices to tensor generators
            config_patches_list: Optional list of config patches per decomposition

        Returns:
            List of SubgraphChoiceCaller instances for autotuning
        """
        if not decompositions:
            return []

        assert len(decompositions) == len(non_tensor_args), (
            f"decompositions and non_tensor_args must have same length, "
            f"got {len(decompositions)} decompositions and {len(non_tensor_args)} kwargs"
        )

        # Default to empty config_patches if not provided
        if config_patches_list is None:
            config_patches_list = [{} for _ in decompositions]

        # Infer layouts and ensure layout consistency for fair autotuning comparison
        layouts = [
            self._infer_custom_op_layout(
                input_nodes, decomp, kwargs, default_impl, input_gen_fns
            )
            for decomp, kwargs in zip(decompositions, non_tensor_args)
        ]

        # Validate all decompositions produce equivalent layouts for fair comparison
        self._validate_layout_equivalence(name, decompositions, layouts)
        layout = layouts[0]  # All layouts are now validated to be equivalent

        choices: list[SubgraphChoiceCaller] = []
        for decomp, decomp_kwargs, config_patches in zip(
            decompositions, non_tensor_args, config_patches_list
        ):
            # Create make_fx_graph function for this decomposition
            # Uses error_on_new_guards to detect impls that add guards
            from torch.fx.experimental.symbolic_shapes import _ShapeEnvGuardError

            def make_fx_graph(
                *args: Any,
                decomp: Callable[..., Any] = decomp,
                decomp_kwargs: dict[str, Any] = decomp_kwargs,
            ) -> Any:
                # decomp_kwargs contains all merged parameters: CustomOpConfig params + runtime kwargs

                from torch.fx.experimental.proxy_tensor import make_fx

                from ..decomposition import select_decomp_table

                decomposition_table = select_decomp_table()
                shape_env = V.fake_mode.shape_env

                # Use error_on_new_guards to detect impls that add guards during tracing
                guard_ctx = (
                    shape_env.error_on_new_guards()
                    if shape_env is not None
                    else contextlib.nullcontext()
                )
                with guard_ctx:
                    return make_fx(
                        functools.partial(decomp, **decomp_kwargs),
                        decomposition_table=decomposition_table,
                        tracing_mode="symbolic",
                    )(*args)

            # Generate descriptive name for this variant
            variant_name = self._generate_variant_name(decomp, decomp_kwargs)

            # Try to create choice; skip if it adds guards
            try:
                choice = self.generate(
                    name=f"{name}_{variant_name}",
                    input_nodes=input_nodes,
                    layout=layout,
                    make_fx_graph=make_fx_graph,
                    description=f"CustomOp {decomp.__name__}",
                    input_gen_fns=input_gen_fns,
                )
            except _ShapeEnvGuardError:
                log.info(
                    "Skipping decomposition %s: adds guards during tracing",
                    decomp.__name__,
                )
                counters["inductor"]["custom_op_decomp_guard_skips"] += 1
                continue

            # Cache decomposition info for range-based dispatch
            choice.cache_decomposition(decomp, decomp_kwargs)
            # Store config_patches for this choice
            choice.config_patches = config_patches
            choices.append(choice)

        return choices