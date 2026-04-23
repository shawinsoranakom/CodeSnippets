def format(cls, profiler, indent: int = 0):
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

        flat_nodes = flatten(profiler.kineto_results.experimental_event_tree())

        # Profiler inserts a `cudaDeviceSynchronize` at the end of profiling.
        # and may also insert 'Context Sync' CUDA synchronization event.
        if flat_nodes and flat_nodes[-2][1] == "cudaDeviceSynchronize":
            flat_nodes = flat_nodes[:-2]

        if flat_nodes and flat_nodes[-1][1] == "cudaDeviceSynchronize":
            flat_nodes = flat_nodes[:-1]

        # Profiler inserts a `hipDeviceSynchronize` at the end of profiling.
        if flat_nodes and flat_nodes[-1][1] == "hipDeviceSynchronize":
            flat_nodes = flat_nodes[:-1]

        min_depth = min(
            [d + 1 for d, name in flat_nodes if "begin_unit_test_marker" in name] or [0]
        )
        return textwrap.indent(
            "\n".join(
                [
                    f"{'  ' * (d - min_depth)}{name.rstrip()}"
                    for d, name in flat_nodes
                    if d >= min_depth
                ]
            ),
            " " * indent,
        )