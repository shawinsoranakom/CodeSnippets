def optimize_block_descriptions() -> dict[str, int]:
    """Generate optimized descriptions for blocks that don't have one yet.

    Uses the shared OpenAI client to rewrite block descriptions into concise
    summaries suitable for agent generation prompts.

    Returns:
        Dict with counts: processed, success, failed, skipped.
    """
    db_client = get_database_manager_client()

    blocks = db_client.get_blocks_needing_optimization()
    if not blocks:
        logger.info("All blocks already have optimized descriptions")
        return {"processed": 0, "success": 0, "failed": 0, "skipped": 0}

    logger.info("Found %d blocks needing optimized descriptions", len(blocks))

    non_empty = [b for b in blocks if b.get("description", "").strip()]
    skipped = len(blocks) - len(non_empty)

    new_descriptions = asyncio.run(_optimize_descriptions(non_empty))

    stats = {
        "processed": len(non_empty),
        "success": len(new_descriptions),
        "failed": len(non_empty) - len(new_descriptions),
        "skipped": skipped,
    }

    logger.info(
        "Block description optimization complete: "
        "%d/%d succeeded, %d failed, %d skipped",
        stats["success"],
        stats["processed"],
        stats["failed"],
        stats["skipped"],
    )

    if new_descriptions:
        for block_id, optimized in new_descriptions.items():
            db_client.update_block_optimized_description(block_id, optimized)

        # Update in-memory descriptions first so the cache rebuilds with fresh data.
        try:
            block_classes = get_blocks()
            for block_id, optimized in new_descriptions.items():
                if block_id in block_classes:
                    block_classes[block_id]._optimized_description = optimized
            logger.info(
                "Updated %d in-memory block descriptions", len(new_descriptions)
            )
        except Exception:
            logger.warning(
                "Could not update in-memory block descriptions", exc_info=True
            )

        from backend.copilot.tools.agent_generator.blocks import (
            reset_block_caches,  # local to avoid circular import
        )

        reset_block_caches()

    return stats