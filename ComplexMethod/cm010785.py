def remove_outputs(
        cur_graph: fx.Graph, cur_inps: Sequence[torch.Tensor], granularity: int
    ) -> ReproState | None:
        granularity = max(1, granularity // 2)
        output: fx.Node | None = None
        for idx, node in enumerate(cur_graph.nodes):
            node.idx = idx  # type: ignore[attr-defined]
            if node.op == "output":
                output = node
                break

        if output is None:
            return None

        if isinstance(output.args[0], fx.Node):
            return None

        # output.args[0] is a tuple/list of nodes when returning multiple outputs
        output_args_raw = output.args[0]
        if not isinstance(output_args_raw, (list, tuple)):
            raise AssertionError(
                f"expected output_args_raw to be list or tuple, got {type(output_args_raw)}"
            )
        output_args = sorted(
            output_args_raw,
            key=lambda x: x.idx if isinstance(x, fx.Node) else int(1e9),  # type: ignore[attr-defined]
        )
        if len(output_args) == 1:
            return None

        for idx in range(0, len(output_args), granularity):
            output.args = (output_args[:idx] + output_args[idx + granularity :],)
            if graph_fails(cur_graph, cur_inps):
                return ReproState(cur_graph, cur_inps)
        return None