def __contains__(self, graph_id: int) -> bool:
        """Check if the given graph ID matches this filter."""
        if graph_id in self._explicit_ids:
            return True

        for op, val in self._conditions:
            if op == ">" and graph_id > val:
                return True
            elif op == ">=" and graph_id >= val:
                return True
            elif op == "<" and graph_id < val:
                return True
            elif op == "<=" and graph_id <= val:
                return True

        return False