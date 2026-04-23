def combo_grid_meta(self, size_hints_list: list[dict[str, int]]) -> dict[str, Any]:
        dynamic_shape = bool(self.dynamic_shape_args)
        num_kernels = len(self.sub_kernels)
        min_blocks = (
            max(self.min_x_blocks_list) * num_kernels if not dynamic_shape else None
        )

        meta: dict[str, Any] = {
            "num_kernels": num_kernels,
            "min_blocks": min_blocks,
        }

        if not self.enable_autotune:
            default_config: dict[str, int] = {}
            if config.combo_kernel_per_subkernel_blocks:
                # Per-subkernel block sizes: XBLOCK_0, XBLOCK_1, etc.
                for num, sub_kernel in enumerate(self.sub_kernels):
                    if sub_kernel.no_x_dim:
                        default_config[f"XBLOCK_{num}"] = 1
                    else:
                        block_size = (
                            self.block_size_2d
                            if any(self.y_tree_list)
                            else self.block_size_1d
                        )
                        default_config[f"XBLOCK_{num}"] = block_size

                    if self.y_tree_list[num]:
                        default_config[f"YBLOCK_{num}"] = self.block_size_2d
            else:
                if "YBLOCK" in self.block_args:
                    default_config = {
                        "XBLOCK": self.block_size_2d,
                        "YBLOCK": self.block_size_2d,
                    }
                else:
                    default_config = {"XBLOCK": self.block_size_1d}
            meta["default_config"] = default_config
        else:
            meta["default_config"] = None

        for num, sub_kernel in enumerate(self.sub_kernels):
            meta[f"no_x_dim_{num}"] = sub_kernel.no_x_dim

            if config.combo_kernel_per_subkernel_blocks:
                meta[f"heuristic_{num}"] = (
                    "persistent_reduction"
                    if sub_kernel.persistent_reduction
                    else "reduction"
                    if sub_kernel.inside_reduction
                    else "pointwise"
                )

                meta[f"size_hints_{num}"] = size_hints_list[num]
                if meta[f"heuristic_{num}"] == "pointwise":
                    if len(size_hints_list[num]) == 2:
                        meta[f"tile_hint_{num}"] = "TileHint.SQUARE"
                    else:
                        meta[f"tile_hint_{num}"] = "TileHint.DEFAULT"
                    if sub_kernel.tiling_scores:
                        meta[f"tiling_scores_{num}"] = {
                            dim: V.graph.sizevars.optimization_hint(score, fallback=1)
                            for dim, score in sub_kernel.tiling_scores.items()
                        }
                else:
                    meta[f"reduction_hint_{num}"] = (
                        sub_kernel.features.get_reduction_hint().name
                    )

            for tree in sub_kernel.range_trees:
                if not tree.is_reduction:
                    numel_name = f"{tree.prefix}numel_{num}"
                    if numel_name in self.dynamic_shape_args:
                        meta[numel_name] = None
                    else:
                        meta[numel_name] = int(V.graph.sizevars.simplify(tree.numel))

        return meta