def generate(self, meta: dict[str, int], is_lazy: bool = False) -> None:
        combo_meta = self.inductor_meta["combo_grid_meta"]
        if combo_meta["default_config"]:
            meta = {**combo_meta["default_config"], **meta}

        total_blocks_list = []
        for num in range(combo_meta["num_kernels"]):
            xnumel = combo_meta[f"xnumel_{num}"]
            assert xnumel is None or xnumel > 0
            xnumel = xnumel or f"xnumel_{num}"
            x_blocks = self.ceildiv(
                xnumel,
                1 if combo_meta[f"no_x_dim_{num}"] else meta.get(f"XBLOCK_{num}"),
            )
            y_blocks = (
                self.ceildiv(
                    combo_meta[f"ynumel_{num}"] or f"ynumel_{num}",
                    meta.get(f"YBLOCK_{num}"),
                )
                if f"ynumel_{num}" in combo_meta
                else 1
            )
            total_blocks_list.append(self.product([x_blocks, y_blocks]))

        self.x_grid = self.summation(total_blocks_list)
        if combo_meta["min_blocks"]:
            self.x_grid = self.maximum([self.x_grid, combo_meta["min_blocks"]])
        self.y_grid = 1
        self.z_grid = 1