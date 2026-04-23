def flatten(nodes, depth=0, out=None):
            if out is None:
                out = []

            for node in nodes:
                cls.validate_node(node)
                name = cls.fmt_name(node.name)
                prune_level = PRUNE_FUNCTIONS.get(name.strip(), None)
                if prune_level is None:
                    out.append((depth, name))
                    flatten(node.children, depth + 1, out)
                elif prune_level == IGNORE:
                    flatten(node.children, depth, out)
                elif prune_level == KEEP_NAME_AND_ELLIPSES:
                    out.append((depth, name))
                    if node.children:
                        out.append((depth + 1, "..."))
                elif prune_level == KEEP_ELLIPSES:
                    out.append((depth, "..."))
                else:
                    if prune_level != PRUNE_ALL:
                        raise AssertionError(f"Expected PRUNE_ALL, got {prune_level}")

            return out