async def get_graph_execution_by_share_token(
    share_token: str,
) -> SharedExecutionResponse | None:
    """Get a shared execution with limited public-safe data."""
    execution = await AgentGraphExecution.prisma().find_first(
        where={
            "shareToken": share_token,
            "isShared": True,
            "isDeleted": False,
        },
        include={
            "AgentGraph": True,
            "NodeExecutions": {
                "include": {
                    "Output": True,
                    "Node": {
                        "include": {
                            "AgentBlock": True,
                        }
                    },
                },
            },
        },
    )

    if not execution:
        return None

    # Extract outputs from OUTPUT blocks only (consistent with GraphExecution.from_db)
    outputs: CompletedBlockOutput = defaultdict(list)
    if execution.NodeExecutions:
        for node_exec in execution.NodeExecutions:
            if node_exec.Node and node_exec.Node.agentBlockId:
                # Get the block definition to check its type
                block = get_block(node_exec.Node.agentBlockId)

                if block and block.block_type == BlockType.OUTPUT:
                    # For OUTPUT blocks, the data is stored in executionData or Input
                    # The executionData contains the structured input with 'name' and 'value' fields
                    if hasattr(node_exec, "executionData") and node_exec.executionData:
                        exec_data = type_utils.convert(
                            node_exec.executionData, BlockInput
                        )
                        if "name" in exec_data:
                            name = exec_data["name"]
                            value = exec_data.get("value")
                            outputs[name].append(value)
                    elif node_exec.Input:
                        # Build input_data from Input relation
                        input_data = {}
                        for data in node_exec.Input:
                            if data.name and data.data is not None:
                                input_data[data.name] = type_utils.convert(
                                    data.data, JsonValue
                                )

                        if "name" in input_data:
                            name = input_data["name"]
                            value = input_data.get("value")
                            outputs[name].append(value)

    return SharedExecutionResponse(
        id=execution.id,
        graph_name=(
            execution.AgentGraph.name
            if (execution.AgentGraph and execution.AgentGraph.name)
            else "Untitled Agent"
        ),
        graph_description=(
            execution.AgentGraph.description if execution.AgentGraph else None
        ),
        status=ExecutionStatus(execution.executionStatus),
        created_at=execution.createdAt,
        outputs=outputs,
    )