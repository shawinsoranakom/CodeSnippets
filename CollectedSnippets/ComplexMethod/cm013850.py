def visit(n: torch.fx.Node) -> Any:
        if n.op == "call_function" and "example_value" not in n.meta:
            # fake tensor validity is checked inside get_fake_value using
            # ensure_graph_fake
            return get_fake_value(n, tx, allow_non_graph_fake)

        elif n.op == "get_attr" and "example_value" not in n.meta:
            assert n.target in tx.output.nn_modules
            gm = tx.output.nn_modules[n.target]  # type: ignore[index]
            assert isinstance(gm, torch.fx.GraphModule)
            return gm

        out = n.meta["example_value"]
        if not allow_non_graph_fake and isinstance(out, torch.Tensor):
            return ensure_graph_fake(out, tx)
        return out