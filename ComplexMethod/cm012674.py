def select_combo_heuristics(
        self, heuristics_list: list[str], size_hints_list: list[dict[str, int]]
    ) -> tuple[str, dict[str, int], TritonKernel]:
        if not self.enable_autotune:
            return "foreach", size_hints_list[0], self.sub_kernels[0]
        if "reduction" in heuristics_list:
            i, _ = max(
                enumerate(size_hints_list),
                key=lambda x: x[1]["x"] if heuristics_list[x[0]] == "reduction" else 0,
            )
            return heuristics_list[i], size_hints_list[i], self.sub_kernels[i]
        elif "pointwise" in heuristics_list:
            i, _ = max(
                enumerate(size_hints_list),
                key=lambda x: x[1]["x"] if heuristics_list[x[0]] == "pointwise" else 0,
            )
            # modify size_hint to avoid oom check fail (may be a false alarm)
            num_pointwise = len([e for e in heuristics_list if e == "pointwise"])
            num_reduction = len([e for e in heuristics_list if e == "reduction"])
            num_persistent_reduction = len(
                [e for e in heuristics_list if e == "persistent_reduction"]
            )
            assert num_reduction == 0, (
                "combining pointwise and reduction are not supported yet."
            )
            heuristics = (
                "pointwise_with_reduction"
                if num_persistent_reduction > 0
                else "pointwise"
            )
            if len(heuristics_list) - num_pointwise >= 4:
                size_hints = size_hints_list[i]
                size_hints["x"] = min(128, size_hints["x"])
            return heuristics, size_hints_list[i], self.sub_kernels[i]
        else:
            # find persistent_reduction with maximum rnumel
            i, _ = max(
                enumerate(size_hints_list),
                key=lambda x: max(
                    (v for k, v in x[1].items() if prefix_is_reduction(k))
                ),
            )
            return heuristics_list[i], size_hints_list[i], self.sub_kernels[i]