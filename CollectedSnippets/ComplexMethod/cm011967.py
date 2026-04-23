def find_smallest_i(graph: fx.Graph, prefix: str) -> int:
        i = 0
        for node in graph.nodes:
            if node.op == "get_attr" and node.target.startswith(prefix):
                if len(node.target) > len(prefix):
                    post_fix = node.target.split(prefix)[-1]
                    if post_fix.isdigit():
                        i = max(i, int(post_fix))
        for key in existing_keys:
            if key.startswith(prefix):
                if len(key) > len(prefix):
                    post_fix = key.split(prefix)[-1]
                    if post_fix.isdigit():
                        i = max(i, int(post_fix))
        return i + 1