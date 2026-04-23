async def get_suggested_blocks(count: int = 5) -> list[BlockInfo]:
    suggested_blocks = []
    # Sum the number of executions for each block type
    # Prisma cannot group by nested relations, so we do a raw query
    # Calculate the cutoff timestamp
    timestamp_threshold = datetime.now(timezone.utc) - timedelta(days=30)

    results = await query_raw_with_schema(
        """
        SELECT
            agent_node."agentBlockId" AS block_id,
            COUNT(execution.id) AS execution_count
        FROM {schema_prefix}"AgentNodeExecution" execution
        JOIN {schema_prefix}"AgentNode" agent_node ON execution."agentNodeId" = agent_node.id
        WHERE execution."endedTime" >= $1::timestamp
        GROUP BY agent_node."agentBlockId"
        ORDER BY execution_count DESC;
        """,
        timestamp_threshold,
    )

    # Get the top blocks based on execution count
    # But ignore Input and Output blocks
    blocks: list[tuple[BlockInfo, int]] = []

    for block_type in load_all_blocks().values():
        block: AnyBlockSchema = block_type()
        if block.disabled or block.block_type in (
            backend.data.block.BlockType.INPUT,
            backend.data.block.BlockType.OUTPUT,
            backend.data.block.BlockType.AGENT,
        ):
            continue
        # Find the execution count for this block
        execution_count = next(
            (row["execution_count"] for row in results if row["block_id"] == block.id),
            0,
        )
        blocks.append((block.get_info(), execution_count))
    # Sort blocks by execution count
    blocks.sort(key=lambda x: x[1], reverse=True)

    suggested_blocks = [block[0] for block in blocks]

    # Return the top blocks
    return suggested_blocks[:count]
