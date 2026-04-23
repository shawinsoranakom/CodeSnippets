def __call__(self, graph: fx.Graph):
        from torch.fx.experimental.symbolic_shapes import is_symbolic

        compile_range = get_pass_context().compile_range
        is_single = compile_range.is_single_size()

        for node in graph.nodes:
            val = node.meta.get("val")
            if val is None:
                val = node.meta.get("example_value")
            if isinstance(val, torch.Tensor):
                has_symbolic = any(is_symbolic(d) for d in val.shape)
                if is_single:
                    assert not has_symbolic, (
                        f"compile_sizes entry {compile_range}: "
                        f"node '{node.name}' has symbolic shape "
                        f"{val.shape}"
                    )
                else:
                    # compile_ranges should have at least some
                    # symbolic shapes (the batch dimension)
                    if has_symbolic:
                        self.num_dynamic_calls += 1
                        return

        if is_single:
            self.num_static_calls += 1