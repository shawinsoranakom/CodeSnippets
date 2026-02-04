async def ensure_block_exists(
    db: Prisma, block_id: str, known_blocks: set[str]
) -> bool:
    """Ensure a block exists in the database, create a placeholder if needed.

    Returns True if the block exists (or was created), False otherwise.
    """
    if block_id in known_blocks:
        return True

    # Check if it already exists in the database
    existing = await db.agentblock.find_unique(where={"id": block_id})
    if existing:
        known_blocks.add(block_id)
        return True

    # Create a placeholder block
    print(f"    Creating placeholder block: {block_id}")
    try:
        await db.agentblock.create(
            data=AgentBlockCreateInput(
                id=block_id,
                name=f"Placeholder_{block_id[:8]}",
                inputSchema="{}",
                outputSchema="{}",
            )
        )
        known_blocks.add(block_id)
        return True
    except Exception as e:
        print(f"    Warning: Could not create placeholder block {block_id}: {e}")
        return False
