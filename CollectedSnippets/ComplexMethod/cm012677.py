def jit_line(
        self,
        heuristics: str,
        size_hints: dict[str, int],
        selected_kernel: TritonKernel,
        signature: list[Any],
        argdefs: list[ArgName],
        size_hints_list: list[dict[str, int]],
        pointwise_with_reduce: bool = False,
    ) -> str:
        """Write the @triton_heuristics.<heuristics> decorator line for the combo kernel."""

        can_use_32bit = all(k.index_dtype == "tl.int32" for k in self.sub_kernels)
        size_dtype = "tl.int32" if can_use_32bit else "tl.int64"
        for i, sub in enumerate(self.sub_kernels):
            self.min_x_blocks_sub_kernel(sub, i)
        self.select_dispatch_strategy()
        triton_meta: dict[str, Any] = {
            "signature": signature_to_meta(
                signature, size_dtype=size_dtype, argdefs=argdefs
            ),
            "device": DeviceProperties.create(V.graph.get_current_device_or_throw()),
            "constants": {},
            # Inherit enable_fp_fusion, launch_pdl, disable_ftz so combo kernels
            # compile with the same Triton options as standalone kernels.
            **TritonKernel.triton_meta_common(),
        }

        for arg_num in equal_1_arg_indices(signature):
            triton_meta["constants"][signature[arg_num].name] = 1  # type: ignore[index,union-attr]

        triton_meta["configs"] = [config_of(signature)]

        mutated_args = self.get_mutated_args_sub_kernels()
        dispatch = self.dispatch_class
        assert dispatch is not None

        # Compute the max persistent R0_BLOCK across sub-kernels.
        # This is used by _reduction_configs() to avoid generating configs
        # where XBLOCK * max_persistent_rblock creates pathologically large
        # tiles that cause extreme ROCm compilation times.
        # The max_persistent_rblock mirrors how R0_BLOCK is computed in
        # codegen_static_numels_sub_kernel() for persistent reductions.
        max_persistent_rblock = 0
        for sub in self.sub_kernels:
            if sub.persistent_reduction:
                for tree in sub.range_trees:
                    if tree.is_reduction:
                        simplified_numel = V.graph.sizevars.simplify(tree.numel)
                        if isinstance(simplified_numel, (Integer, int)):
                            val = next_power_of_2(int(simplified_numel))
                            max_persistent_rblock = max(max_persistent_rblock, val)

        inductor_meta = {
            "grid_type": dispatch.grid_expr.__name__,
            "combo_grid_meta": self.combo_grid_meta(size_hints_list),
            "kernel_name": str(Placeholder.DESCRIPTIVE_NAME),
            "mutated_arg_names": mutated_args,
            # Matches triton.py:codegen_kernel(): inference/backward graphs skip
            # CPU-copy of mutated args during autotune retries; training-forward
            # graphs must keep it to preserve benchmark inputs across retries.
            "optimize_mem": V.graph.is_inference or V.graph.is_backward,
            **self.triton_kernel_cls.inductor_meta_common(),
        }
        if max_persistent_rblock > 0:
            inductor_meta["max_persistent_rblock"] = max_persistent_rblock

        sub_kernel = selected_kernel
        if heuristics == "foreach":
            heuristics_line = f"""
                @triton_heuristics.foreach(
                    filename=__file__,
                    triton_meta={triton_meta!r},
                    inductor_meta={inductor_meta!r},
                )
                @triton.jit
            """
        elif sub_kernel.inside_reduction:
            reduction_hint = sub_kernel.features.get_reduction_hint()
            heuristics_line = f"""
                @triton_heuristics.{heuristics}(
                    size_hints={size_hints!r},
                    reduction_hint={reduction_hint},
                    filename=__file__,
                    triton_meta={triton_meta!r},
                    inductor_meta={inductor_meta!r}
                )
                @triton.jit
            """
        else:
            tile_hint = ""
            if len(size_hints) == 2:
                tile_hint = "tile_hint=TileHint.SQUARE,"
            else:
                tile_hint = "tile_hint=TileHint.DEFAULT,"
            heuristics_line = f"""
                @triton_heuristics.{heuristics}(
                    size_hints={size_hints!r}, {tile_hint}
                    filename=__file__,
                    triton_meta={triton_meta!r},
                    inductor_meta={inductor_meta!r}
                )
                @triton.jit
            """

        self.triton_meta = triton_meta
        self.inductor_meta = inductor_meta

        return heuristics_line