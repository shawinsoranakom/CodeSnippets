def _walk(node, path):
        for prefix, child in node.items():
            yield from _walk(child, [*path, prefix])
        if not node:
            yield Path(*path)