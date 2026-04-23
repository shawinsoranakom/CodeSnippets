async def get_graph_execution_results(
    graph_id: str,
    graph_exec_id: str,
    auth: APIAuthorizationInfo = Security(
        require_permission(APIKeyPermission.READ_GRAPH)
    ),
) -> GraphExecutionResult:
    graph_exec = await execution_db.get_graph_execution(
        user_id=auth.user_id,
        execution_id=graph_exec_id,
        include_node_executions=True,
    )
    if not graph_exec:
        raise HTTPException(
            status_code=404, detail=f"Graph execution #{graph_exec_id} not found."
        )

    if not await graph_db.get_graph(
        graph_id=graph_exec.graph_id,
        version=graph_exec.graph_version,
        user_id=auth.user_id,
    ):
        raise HTTPException(status_code=404, detail=f"Graph #{graph_id} not found.")

    return GraphExecutionResult(
        execution_id=graph_exec_id,
        status=graph_exec.status.value,
        nodes=[
            ExecutionNode(
                node_id=node_exec.node_id,
                input=node_exec.input_data.get("value", node_exec.input_data),
                output={k: v for k, v in node_exec.output_data.items()},
            )
            for node_exec in graph_exec.node_executions
        ],
        output=(
            [
                {name: value}
                for name, values in graph_exec.outputs.items()
                for value in values
            ]
            if graph_exec.status == AgentExecutionStatus.COMPLETED
            else None
        ),
    )