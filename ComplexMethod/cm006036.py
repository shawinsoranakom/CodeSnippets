def assert_execution_equivalence(
    trace1: ExecutionTrace,
    trace2: ExecutionTrace,
    *,
    allow_parallel_reordering: bool = True,
) -> None:
    """Assert that two execution traces are equivalent.

    Args:
        trace1: First execution trace
        trace2: Second execution trace
        allow_parallel_reordering: If True, allows vertices in the same layer
                                  to execute in different orders (since they run
                                  in parallel in the arun path)
    """
    # Both should succeed or both should fail
    if trace1.error or trace2.error:
        assert (trace1.error is None) == (trace2.error is None), (
            f"{trace1.path_name} error: {trace1.error}, {trace2.path_name} error: {trace2.error}"
        )

    # Should execute the same set of vertices
    vertices1 = set(trace1.vertices_executed)
    vertices2 = set(trace2.vertices_executed)

    assert vertices1 == vertices2, (
        f"Different vertices executed:\n"
        f"{trace1.path_name}: {vertices1}\n"
        f"{trace2.path_name}: {vertices2}\n"
        f"Only in {trace1.path_name}: {vertices1 - vertices2}\n"
        f"Only in {trace2.path_name}: {vertices2 - vertices1}"
    )

    # Should execute each vertex the same number of times
    for vertex_id in vertices1:
        count1 = trace1.get_vertex_run_count(vertex_id)
        count2 = trace2.get_vertex_run_count(vertex_id)

        assert count1 == count2, (
            f"Vertex {vertex_id} executed different number of times:\n"
            f"{trace1.path_name}: {count1} times\n"
            f"{trace2.path_name}: {count2} times"
        )

    # If not allowing reordering, execution order should be identical
    if not allow_parallel_reordering:
        assert trace1.execution_order == trace2.execution_order, (
            f"Execution order differs:\n"
            f"{trace1.path_name}: {trace1.execution_order}\n"
            f"{trace2.path_name}: {trace2.execution_order}"
        )