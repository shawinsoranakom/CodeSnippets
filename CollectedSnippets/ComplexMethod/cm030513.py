def _extract_elided_nodes(self, node, path):
        """Remove non-elided nodes and recalculate values bottom-up."""
        if not node:
            return False

        func_key = self._extract_func_key(node, self._baseline_collector._string_table)
        current_path = path + (func_key,) if func_key else path

        is_elided = current_path in self._elided_paths if func_key else False

        if "children" in node:
            # Filter children, keeping only those with elided descendants
            elided_children = []
            total_value = 0
            for child in node["children"]:
                if self._extract_elided_nodes(child, current_path):
                    elided_children.append(child)
                    total_value += child.get("value", 0)
            node["children"] = elided_children

            # Recalculate value for structural (non-elided) ancestor nodes;
            # elided nodes keep their original value to preserve self-samples
            if elided_children and not is_elided:
                node["value"] = total_value

        # Keep this node if it's elided or has elided descendants
        return is_elided or bool(node.get("children"))