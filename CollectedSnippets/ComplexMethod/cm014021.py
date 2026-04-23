def get_graph_sizes(self, name: str) -> str:
        graph_sizes_str = "TRACED GRAPH TENSOR SIZES\n"
        graph_sizes_str += f"===== {name} =====\n"
        for node in self.graph.nodes:
            example_value = node.meta.get("example_value", None)
            if isinstance(example_value, torch._subclasses.FakeTensor):
                size = example_value.shape
                graph_sizes_str += f"{node.name}: {tuple(size)}\n"
                concrete_size = []
                has_symint = False
                for sz in size:
                    if isinstance(sz, int):
                        concrete_size.append(sz)
                    elif isinstance(sz, torch.SymInt):
                        has_symint = True
                        concrete_size.append(sz.node.hint)
                    else:
                        break
                else:
                    if has_symint:
                        graph_sizes_str += (
                            f"{node.name} (concrete): {tuple(concrete_size)}\n"
                        )
        return graph_sizes_str