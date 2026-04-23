def add_control_deps(graph):
            nodes = [n for n in graph.nodes if n.op == "call_function"]
            if len(nodes) != 3:
                raise AssertionError(f"Expected 3 nodes, got {len(nodes)}")
            c_node = nodes[0]
            d_node = nodes[1]
            e_node = nodes[2]

            if d_node.target != torch.ops.aten.mm.default:
                raise AssertionError(f"Expected mm.default, got {d_node.target}")

            from torch.utils._ordered_set import OrderedSet

            deps_map = {d_node: OrderedSet([c_node]), e_node: OrderedSet([d_node])}
            torch._inductor.fx_passes.control_dependencies.preserve_node_ordering(
                graph, deps_map
            )
            sub_g = graph.find_nodes(
                op="call_function", target=torch.ops.higher_order.control_deps
            )
            if len(sub_g) != 2:
                raise AssertionError(f"Expected 2 control_deps nodes, got {len(sub_g)}")

            if list(sub_g[0].meta["val"].shape) != [256, 256]:
                raise AssertionError(
                    f"Expected shape [256, 256], got {list(sub_g[0].meta['val'].shape)}"
                )
            if list(sub_g[1].meta["val"].shape) != [256, 256]:
                raise AssertionError(
                    f"Expected shape [256, 256], got {list(sub_g[1].meta['val'].shape)}"
                )

            for attr in graph.find_nodes(op="get_attr"):
                for n in getattr(graph.owning_module, attr.target).graph.nodes:
                    if list(n.meta["val"].shape) != [256, 256]:
                        raise AssertionError(
                            f"Expected shape [256, 256], got {list(n.meta['val'].shape)}"
                        )

            return graph