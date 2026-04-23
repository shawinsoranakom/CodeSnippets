def generate(self, meta: dict[str, int], is_lazy: bool = False) -> None:
        combo_meta = self.inductor_meta["combo_grid_meta"]
        if combo_meta["default_config"]:
            meta = {**combo_meta["default_config"], **meta}
        no_x_dims = []
        xnumels = []
        ynumels = []

        for num in range(combo_meta["num_kernels"]):
            assert (
                combo_meta[f"xnumel_{num}"] is None or combo_meta[f"xnumel_{num}"] > 0
            )
            no_x_dims.append(combo_meta[f"no_x_dim_{num}"])
            xnumels.append(combo_meta[f"xnumel_{num}"] or f"xnumel_{num}")
            if f"ynumel_{num}" in combo_meta:
                ynumels.append(combo_meta[f"ynumel_{num}"] or f"ynumel_{num}")

        self.x_grid = self.combo_x_grid(xnumels, no_x_dims, meta)
        if combo_meta["min_blocks"]:
            self.x_grid = self.maximum([self.x_grid, combo_meta["min_blocks"]])
        if ynumels:
            self.prefix.extend(
                [
                    self.assign_tmp(
                        "y_grid_raw_",
                        self.ceildiv(self.maximum(ynumels), meta.get("YBLOCK")),
                    ),
                    self.assign_tmp(
                        "y_grid_div_", self.ceildiv("y_grid_raw_", get_max_y_grid())
                    ),
                ]
            )
            ceildiv_expr = self.ceildiv("y_grid_raw_", "y_grid_div_")
            if self.mode == "python":
                self.y_grid = f"(0 if y_grid_div_ == 0 else {ceildiv_expr})"
            else:
                self.y_grid = f"(y_grid_div_ == 0 ? 0 : {ceildiv_expr})"
            self.z_grid = "y_grid_div_"