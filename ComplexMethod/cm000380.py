def ensure_embeddings_coverage():
    """
    Ensure all content types (store agents, blocks, docs) have embeddings for search.

    Processes ALL missing embeddings in batches of 10 per content type until 100% coverage.
    Missing embeddings = content invisible in hybrid search.

    Schedule: Runs every 6 hours (balanced between coverage and API costs).
    - Catches new content added between scheduled runs
    - Batch size 10 per content type: gradual processing to avoid rate limits
    - Manual trigger available via execute_ensure_embeddings_coverage endpoint
    """
    db_client = get_database_manager_client()
    stats = db_client.get_embedding_stats()

    # Check for error from get_embedding_stats() first
    if "error" in stats:
        logger.error(
            f"Failed to get embedding stats: {stats['error']} - skipping backfill"
        )
        return {
            "backfill": {"processed": 0, "success": 0, "failed": 0},
            "cleanup": {"deleted": 0},
            "error": stats["error"],
        }

    # Extract totals from new stats structure
    totals = stats.get("totals", {})
    without_embeddings = totals.get("without_embeddings", 0)
    coverage_percent = totals.get("coverage_percent", 0)

    total_processed = 0
    total_success = 0
    total_failed = 0

    if without_embeddings == 0:
        logger.info("All content has embeddings, skipping backfill")
    else:
        # Log per-content-type stats for visibility
        by_type = stats.get("by_type", {})
        for content_type, type_stats in by_type.items():
            if type_stats.get("without_embeddings", 0) > 0:
                logger.info(
                    f"{content_type}: {type_stats['without_embeddings']} items without embeddings "
                    f"({type_stats['coverage_percent']}% coverage)"
                )

        logger.info(
            f"Total: {without_embeddings} items without embeddings "
            f"({coverage_percent}% coverage) - processing all"
        )

        # Process in batches until no more missing embeddings
        while True:
            result = db_client.backfill_missing_embeddings(batch_size=100)

            total_processed += result["processed"]
            total_success += result["success"]
            total_failed += result["failed"]

            if result["processed"] == 0:
                # No more missing embeddings
                break

            if result["success"] == 0 and result["processed"] > 0:
                # All attempts in this batch failed - stop to avoid infinite loop
                logger.error(
                    f"All {result['processed']} embedding attempts failed - stopping backfill"
                )
                break

            # Small delay between batches to avoid rate limits
            time.sleep(1)

        logger.info(
            f"Embedding backfill completed: {total_success}/{total_processed} succeeded, "
            f"{total_failed} failed"
        )

    # Clean up orphaned embeddings for blocks and docs
    logger.info("Running cleanup for orphaned embeddings (blocks/docs)...")
    cleanup_result = db_client.cleanup_orphaned_embeddings()
    cleanup_totals = cleanup_result.get("totals", {})
    cleanup_deleted = cleanup_totals.get("deleted", 0)

    if cleanup_deleted > 0:
        logger.info(f"Cleanup completed: deleted {cleanup_deleted} orphaned embeddings")
        by_type = cleanup_result.get("by_type", {})
        for content_type, type_result in by_type.items():
            if type_result.get("deleted", 0) > 0:
                logger.info(
                    f"{content_type}: deleted {type_result['deleted']} orphaned embeddings"
                )
    else:
        logger.info("Cleanup completed: no orphaned embeddings found")

    return {
        "backfill": {
            "processed": total_processed,
            "success": total_success,
            "failed": total_failed,
        },
        "cleanup": {
            "deleted": cleanup_deleted,
        },
    }