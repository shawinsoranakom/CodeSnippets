async def initialize_blocks() -> None:
    from backend.blocks import get_blocks
    from backend.sdk.cost_integration import sync_all_provider_costs
    from backend.util.retry import func_retry

    sync_all_provider_costs()

    @func_retry
    async def sync_block_to_db(block: "AnyBlockSchema") -> None:
        existing_block = await AgentBlock.prisma().find_first(
            where={"OR": [{"id": block.id}, {"name": block.name}]}
        )
        if not existing_block:
            await AgentBlock.prisma().create(
                data=AgentBlockCreateInput(
                    id=block.id,
                    name=block.name,
                    inputSchema=json.dumps(block.input_schema.jsonschema()),
                    outputSchema=json.dumps(block.output_schema.jsonschema()),
                    description=block.description,
                )
            )
            return

        input_schema = json.dumps(block.input_schema.jsonschema())
        output_schema = json.dumps(block.output_schema.jsonschema())
        if (
            block.id != existing_block.id
            or block.name != existing_block.name
            or input_schema != existing_block.inputSchema
            or output_schema != existing_block.outputSchema
            or block.description != existing_block.description
        ):
            await AgentBlock.prisma().update(
                where={"id": existing_block.id},
                data={
                    "id": block.id,
                    "name": block.name,
                    "inputSchema": input_schema,
                    "outputSchema": output_schema,
                    "description": block.description,
                    "optimizedDescription": None,
                },
            )

    failed_blocks: list[str] = []
    for cls in get_blocks().values():
        block = cls()
        try:
            await sync_block_to_db(block)
        except Exception as e:
            logger.warning(
                f"Failed to sync block {block.name} to database: {e}. "
                "Block is still available in memory.",
                exc_info=True,
            )
            failed_blocks.append(block.name)

    if failed_blocks:
        logger.error(
            f"Failed to sync {len(failed_blocks)} block(s) to database: "
            f"{', '.join(failed_blocks)}. These blocks are still available in memory."
        )

    # Load optimized descriptions from DB onto block classes so that
    # every get_block() instance automatically carries them.
    try:
        all_db_blocks = await AgentBlock.prisma().find_many(
            where={"optimizedDescription": {"not": None}},
        )
        block_classes = get_blocks()
        applied = 0
        for db_block in all_db_blocks:
            if db_block.optimizedDescription and db_block.id in block_classes:
                block_classes[db_block.id]._optimized_description = (
                    db_block.optimizedDescription
                )
                applied += 1
        if applied:
            logger.info("Loaded %d optimized block descriptions", applied)
    except Exception:
        logger.error("Could not load optimized descriptions", exc_info=True)