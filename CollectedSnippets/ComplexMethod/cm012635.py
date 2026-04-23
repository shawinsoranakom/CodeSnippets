def _generate_lazy_grid(self, prefix: IndentedBuffer) -> None:
        """Generate grid computation code for lazy-compiled kernels."""
        kernel_name = self.kernel_name
        grid_type = self.inductor_meta.get("grid_type") if self.inductor_meta else None

        # For PrecomputedGrid, generate switch statement on config_index
        if grid_type == "PrecomputedGrid":
            assert self.inductor_meta is not None
            precomputed_grids = self.inductor_meta.get("precomputed_grids", [])
            extra_launcher_args = self.inductor_meta.get("extra_launcher_args", [])

            switch_cases = []
            for idx, entry in enumerate(precomputed_grids):
                cpp_grids = list(entry.get("cpp", ["1L", "1L", "1L"]))
                # Replace internal arg names with C++ parameter names
                # e.g., _launcher_s0 -> _grid_0
                for i, arg_name in enumerate(extra_launcher_args):
                    cpp_grids = [g.replace(arg_name, f"_grid_{i}") for g in cpp_grids]
                g0 = cpp_grids[0]
                g1 = cpp_grids[1] if len(cpp_grids) > 1 else "1"
                g2 = cpp_grids[2] if len(cpp_grids) > 2 else "1"
                switch_cases.append(
                    f"case {idx}: grid_0 = {g0}; grid_1 = {g1}; grid_2 = {g2}; break;"
                )
            switch_cases.append("default: grid_0 = 1; grid_1 = 1; grid_2 = 1; break;")
            switch_body = "\n                        ".join(switch_cases)

            prefix.splice(
                f"""\
                uint32_t grid_0, grid_1, grid_2;
                switch ({kernel_name}_result.config_index) {{
                    {switch_body}
                }}
                if (grid_0 == 0) return;
                """
            )
        else:
            from ..runtime.triton_heuristics import GridExpr

            grid = GridExpr.from_meta_lazy(self.inductor_meta, kernel_name)
            for line in grid.prefix:
                prefix.writeline(line)

            prefix.splice(
                f"""\
                uint32_t grid_0 = {grid.x_grid};
                uint32_t grid_1 = {grid.y_grid};
                uint32_t grid_2 = {grid.z_grid};
                if (grid_0 == 0) return;
                """
            )