def _compute_run_manager_delta(self, before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
        """Compute what changed in run_manager state.

        Returns:
            Dictionary with only the changes
        """
        delta = {}

        # Check run_predecessors changes
        before_pred = before.get("run_predecessors", {})
        after_pred = after.get("run_predecessors", {})
        pred_changes = {}
        for vertex_id in set(list(before_pred.keys()) + list(after_pred.keys())):
            before_deps = set(before_pred.get(vertex_id, []))
            after_deps = set(after_pred.get(vertex_id, []))
            if before_deps != after_deps:
                pred_changes[vertex_id] = {
                    "added": list(after_deps - before_deps),
                    "removed": list(before_deps - after_deps),
                }
        if pred_changes:
            delta["run_predecessors"] = pred_changes

        # Check run_map changes
        before_map = before.get("run_map", {})
        after_map = after.get("run_map", {})
        map_changes = {}
        for vertex_id in set(list(before_map.keys()) + list(after_map.keys())):
            before_deps = set(before_map.get(vertex_id, []))
            after_deps = set(after_map.get(vertex_id, []))
            if before_deps != after_deps:
                map_changes[vertex_id] = {
                    "added": list(after_deps - before_deps),
                    "removed": list(before_deps - after_deps),
                }
        if map_changes:
            delta["run_map"] = map_changes

        # Check vertices_to_run changes
        before_to_run = set(before.get("vertices_to_run", set()))
        after_to_run = set(after.get("vertices_to_run", set()))
        if before_to_run != after_to_run:
            delta["vertices_to_run"] = {
                "added": list(after_to_run - before_to_run),
                "removed": list(before_to_run - after_to_run),
            }

        # Check vertices_being_run changes
        before_being_run = set(before.get("vertices_being_run", set()))
        after_being_run = set(after.get("vertices_being_run", set()))
        if before_being_run != after_being_run:
            delta["vertices_being_run"] = {
                "added": list(after_being_run - before_being_run),
                "removed": list(before_being_run - after_being_run),
            }

        return delta