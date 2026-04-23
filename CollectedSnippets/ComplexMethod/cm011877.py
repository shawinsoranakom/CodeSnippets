def check_and_add_duplicate_pattern(
    pattern: PatternExpr,
    graph: torch.fx.Graph | None,
    seen_patterns: dict[str, list[str | None]],
    skip_duplicates: bool = False,
) -> bool:
    """
    Check if a pattern is a duplicate. Because we ignore certain types in searching, but not
    in matching, use the graph to distinguish equivalent search patterns.

    Returns True if a duplicate is found and `skip_duplicates=True` is passed in. Errors if
    `skip_duplicates` is False and a duplicate is found.
    """

    pattern_repr = PatternPrettyPrinter.run(pattern)
    equiv_pattern_reprs = seen_patterns.get(pattern_repr)
    if not equiv_pattern_reprs:
        seen_patterns[pattern_repr].append(str(graph) if graph else None)
        return False

    if graph is None:
        if skip_duplicates:
            return True
        torch._check(
            False,
            lambda: f"Duplicate pattern: {pattern_repr} with no graph",
        )

    new_graph_str = str(graph)
    for graph_str in equiv_pattern_reprs:
        if new_graph_str != graph_str:
            continue
        if skip_duplicates:
            return True
        torch._check(
            False,
            lambda: f"Duplicate pattern: {pattern_repr} with duplicated match graph {graph_str} ",
        )
    equiv_pattern_reprs.append(new_graph_str)
    return False