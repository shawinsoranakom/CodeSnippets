async def backfill_all_content_types(batch_size: int = 10) -> dict[str, Any]:
    """
    Generate embeddings for all content types using registered handlers.

    Processes content types in order: BLOCK → STORE_AGENT → DOCUMENTATION.
    This ensures foundational content (blocks) are searchable first.

    Args:
        batch_size: Number of embeddings to generate per content type

    Returns:
        Dict with stats per content type and overall totals
    """
    results_by_type = {}
    total_processed = 0
    total_success = 0
    total_failed = 0
    all_errors: dict[str, int] = {}  # Aggregate errors across all content types

    # Process content types in explicit order
    processing_order = [
        ContentType.BLOCK,
        ContentType.STORE_AGENT,
        ContentType.DOCUMENTATION,
    ]

    for content_type in processing_order:
        handler = CONTENT_HANDLERS.get(content_type)
        if not handler:
            logger.warning(f"No handler registered for {content_type.value}")
            continue
        try:
            logger.info(f"Processing {content_type.value} content type...")

            # Get missing items from handler
            missing_items = await handler.get_missing_items(batch_size)

            if not missing_items:
                results_by_type[content_type.value] = {
                    "processed": 0,
                    "success": 0,
                    "failed": 0,
                    "message": "No missing embeddings",
                }
                continue

            # Process embeddings concurrently for better performance
            embedding_tasks = [
                ensure_content_embedding(
                    content_type=item.content_type,
                    content_id=item.content_id,
                    searchable_text=item.searchable_text,
                    metadata=item.metadata,
                    user_id=item.user_id,
                )
                for item in missing_items
            ]

            results = await asyncio.gather(*embedding_tasks, return_exceptions=True)

            success = sum(1 for result in results if result is True)
            failed = len(results) - success

            # Aggregate errors across all content types
            if failed > 0:
                for result in results:
                    if isinstance(result, Exception):
                        error_key = f"{type(result).__name__}: {str(result)}"
                        all_errors[error_key] = all_errors.get(error_key, 0) + 1

            results_by_type[content_type.value] = {
                "processed": len(missing_items),
                "success": success,
                "failed": failed,
                "message": f"Backfilled {success} embeddings, {failed} failed",
            }

            total_processed += len(missing_items)
            total_success += success
            total_failed += failed

            logger.info(
                f"{content_type.value}: processed {len(missing_items)}, "
                f"success {success}, failed {failed}"
            )

        except Exception as e:
            logger.error(f"Failed to process {content_type.value}: {e}")
            results_by_type[content_type.value] = {
                "processed": 0,
                "success": 0,
                "failed": 0,
                "error": str(e),
            }

    # Log aggregated errors once at the end
    if all_errors:
        error_details = ", ".join(
            f"{error} ({count}x)" for error, count in all_errors.items()
        )
        logger.error(f"Embedding backfill errors: {error_details}")

    return {
        "by_type": results_by_type,
        "totals": {
            "processed": total_processed,
            "success": total_success,
            "failed": total_failed,
            "message": f"Overall: {total_success} succeeded, {total_failed} failed",
        },
    }