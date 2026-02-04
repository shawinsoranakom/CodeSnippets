async def initialize_blocks(db: Prisma) -> set[str]:
    """Initialize agent blocks in the database from the registered blocks.

    Returns a set of block IDs that exist in the database.
    """
    from backend.data.block import get_blocks

    print("  Initializing agent blocks...")
    blocks = get_blocks()
    created_count = 0
    block_ids = set()

    for block_cls in blocks.values():
        block = block_cls()
        block_ids.add(block.id)
        existing_block = await db.agentblock.find_first(
            where={"OR": [{"id": block.id}, {"name": block.name}]}
        )
        if not existing_block:
            await db.agentblock.create(
                data=AgentBlockCreateInput(
                    id=block.id,
                    name=block.name,
                    inputSchema=json.dumps(block.input_schema.jsonschema()),
                    outputSchema=json.dumps(block.output_schema.jsonschema()),
                )
            )
            created_count += 1
        elif block.id != existing_block.id or block.name != existing_block.name:
            await db.agentblock.update(
                where={"id": existing_block.id},
                data={
                    "id": block.id,
                    "name": block.name,
                    "inputSchema": json.dumps(block.input_schema.jsonschema()),
                    "outputSchema": json.dumps(block.output_schema.jsonschema()),
                },
            )

    print(f"  Initialized {len(blocks)} blocks ({created_count} new)")
    return block_ids
