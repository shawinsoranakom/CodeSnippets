def _match_literals(self, pn: Any, gn: Any, match: InternalMatch) -> bool:
        if isinstance(pn, Node) and isinstance(gn, Node):
            raise AssertionError("pn and gn cannot both be Node")

        if isinstance(pn, Node) and not isinstance(gn, Node):
            if pn.op == "placeholder":
                # Check if we've already matched these nodes in the current
                # traversal
                if pn in match.nodes_map:
                    return match.nodes_map[pn] == gn

                match.nodes_map[pn] = gn
                return True
            else:
                return False
        elif not isinstance(pn, Node) and isinstance(gn, Node):
            return False
        else:
            return type(gn) is type(pn) and gn == pn