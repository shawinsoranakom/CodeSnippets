def find_reduce_scatter_patterns(graph: torch.fx.Graph):
    c10d = torch.ops._c10d_functional

    def reduce_scatter_template(inp: PatternExpr, users: int):
        return CallFunction(
            c10d.wait_tensor.default,
            CallFunction(
                c10d.reduce_scatter_tensor.default,
                inp,
                KeywordArg("reduce_op"),
                Ignored(),
                KeywordArg("group_name"),
                _users=users,
            ),
        )

    # Matches funcol.reduce_scatter_tensor with scatter_dim == 0
    zero_dim_reduce_scatter_pattern_single_user = reduce_scatter_template(
        KeywordArg("input"), users=1
    )

    # Two users will occur when the reduce-scatter result is saved for backward
    zero_dim_reduce_scatter_pattern_multi_user = reduce_scatter_template(
        KeywordArg("input"), users=2
    )

    # Matches funcol.reduce_scatter_tensor with scatter_dim > 0
    non_zero_dim_reduce_scatter_pattern_single_user = reduce_scatter_template(
        CallFunction(
            aten.cat.default,
            ListOf(
                CallFunction(
                    operator.getitem,
                    CallFunction(
                        aten.split.Tensor,
                        KeywordArg("input"),
                        Ignored(),
                        KeywordArg("scatter_dim"),
                        _users=MULTIPLE,
                    ),
                    Ignored(),
                )
            ),
        ),
        users=1,
    )

    # Two users will occur when the reduce-scatter result is saved for backward
    non_zero_dim_reduce_scatter_pattern_multi_user = reduce_scatter_template(
        CallFunction(
            aten.cat.default,
            ListOf(
                CallFunction(
                    operator.getitem,
                    CallFunction(
                        aten.split.Tensor,
                        KeywordArg("input"),
                        Ignored(),
                        KeywordArg("scatter_dim"),
                        _users=MULTIPLE,
                    ),
                    Ignored(),
                )
            ),
        ),
        users=2,
    )

    reduce_scatters = []
    for node in reversed(graph.nodes):
        if node.target == c10d.wait_tensor.default:
            if match := non_zero_dim_reduce_scatter_pattern_single_user.match(node):
                assert isinstance(match, Match)
                reduce_scatters.append(
                    _ReduceScatterMatch(
                        match=match,
                        input_node=match.kwargs["input"],
                        reduce_scatter_node=match.nodes[-2],
                        wait_tensor_node=node,
                        reduce_op=match.kwargs["reduce_op"],
                        scatter_dim=match.kwargs["scatter_dim"],
                        group_name=match.kwargs["group_name"],
                    )
                )
            elif match := zero_dim_reduce_scatter_pattern_single_user.match(node):
                assert isinstance(match, Match)
                reduce_scatters.append(
                    _ReduceScatterMatch(
                        match=match,
                        input_node=match.kwargs["input"],
                        reduce_scatter_node=match.nodes[0],
                        wait_tensor_node=node,
                        reduce_op=match.kwargs["reduce_op"],
                        scatter_dim=0,
                        group_name=match.kwargs["group_name"],
                    )
                )
            elif match := non_zero_dim_reduce_scatter_pattern_multi_user.match(node):
                assert isinstance(match, Match)
                reduce_scatters.append(
                    _ReduceScatterMatch(
                        match=match,
                        input_node=match.kwargs["input"],
                        reduce_scatter_node=match.nodes[-2],
                        wait_tensor_node=node,
                        reduce_op=match.kwargs["reduce_op"],
                        scatter_dim=match.kwargs["scatter_dim"],
                        group_name=match.kwargs["group_name"],
                    )
                )
            elif match := zero_dim_reduce_scatter_pattern_multi_user.match(node):
                assert isinstance(match, Match)
                reduce_scatters.append(
                    _ReduceScatterMatch(
                        match=match,
                        input_node=match.kwargs["input"],
                        reduce_scatter_node=match.nodes[0],
                        wait_tensor_node=node,
                        reduce_op=match.kwargs["reduce_op"],
                        scatter_dim=0,
                        group_name=match.kwargs["group_name"],
                    )
                )
    return list(reversed(reduce_scatters))