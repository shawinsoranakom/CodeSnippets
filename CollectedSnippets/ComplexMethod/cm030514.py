def _add_elided_metadata(self, node, baseline_stats, scale, path):
        """Add differential metadata showing this path disappeared."""
        if not node:
            return

        func_key = self._extract_func_key(node, self._baseline_collector._string_table)
        current_path = path + (func_key,) if func_key else path

        if func_key and current_path in baseline_stats:
            baseline_data = baseline_stats[current_path]
            baseline_self = baseline_data["self"] * scale
            baseline_total = baseline_data["total"] * scale

            node["baseline"] = baseline_self
            node["baseline_total"] = baseline_total
            node["diff"] = -baseline_self
        else:
            node["baseline"] = 0
            node["baseline_total"] = 0
            node["diff"] = 0

        node["self_time"] = 0
        # Elided paths have zero current self-time, so the change is always
        # -100% when there was actual baseline self-time to lose.
        # For internal nodes with no baseline self-time, use 0% to avoid
        # misleading tooltips.
        if baseline_self > 0:
            node["diff_pct"] = -100.0
        else:
            node["diff_pct"] = 0.0

        if "children" in node and node["children"]:
            for child in node["children"]:
                self._add_elided_metadata(child, baseline_stats, scale, current_path)