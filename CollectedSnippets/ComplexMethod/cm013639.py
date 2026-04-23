def _nodes_are_equal(self, pn: Node, gn: Node, node_name_match: str = "") -> bool:
        # if exact match for placeholder is not required, then use placeholder as a wildcard
        if not self.match_placeholder and pn.op == "placeholder":
            return True

        if node_name_match and node_name_match in gn.name:
            return True

        if pn.op == gn.op:
            if pn.op == "placeholder" or pn.op == "output":
                return True
            elif pn.op == "get_attr":
                return self._match_attributes(pn, gn)
            return pn.target == gn.target
        return False