async def cleanup_orphaned_embeddings() -> dict[str, Any]:
    """
    Clean up embeddings for content that no longer exists or is no longer valid.

    Compares current content with embeddings in database and removes orphaned records:
    - STORE_AGENT: Removes embeddings for rejected/deleted store listings
    - BLOCK: Removes embeddings for blocks no longer registered
    - DOCUMENTATION: Removes embeddings for deleted doc files

    Returns:
        Dict with cleanup statistics per content type
    """
    results_by_type = {}
    total_deleted = 0

    # Cleanup orphaned embeddings for all content types
    cleanup_types = [
        ContentType.STORE_AGENT,
        ContentType.BLOCK,
        ContentType.DOCUMENTATION,
    ]

    for content_type in cleanup_types:
        try:
            handler = CONTENT_HANDLERS.get(content_type)
            if not handler:
                logger.warning(f"No handler registered for {content_type}")
                results_by_type[content_type.value] = {
                    "deleted": 0,
                    "error": "No handler registered",
                }
                continue

            # Get all current content IDs from handler
            if content_type == ContentType.STORE_AGENT:
                # Get IDs of approved store listing versions from non-deleted listings
                valid_agents = await query_raw_with_schema(
                    """
                    SELECT slv.id
                    FROM {schema_prefix}"StoreListingVersion" slv
                    JOIN {schema_prefix}"StoreListing" sl ON slv."storeListingId" = sl.id
                    WHERE slv."submissionStatus" = 'APPROVED'
                      AND slv."isDeleted" = false
                      AND sl."isDeleted" = false
                    """,
                )
                current_ids = {row["id"] for row in valid_agents}
            elif content_type == ContentType.BLOCK:
                current_ids = set(get_blocks().keys())
            elif content_type == ContentType.DOCUMENTATION:
                # Use DocumentationHandler to get section-based content IDs
                from backend.api.features.store.content_handlers import (
                    DocumentationHandler,
                )

                doc_handler = CONTENT_HANDLERS.get(ContentType.DOCUMENTATION)
                if isinstance(doc_handler, DocumentationHandler):
                    docs_root = doc_handler._get_docs_root()
                    if docs_root.exists():
                        current_ids = doc_handler._get_all_section_content_ids(
                            docs_root
                        )
                    else:
                        current_ids = set()
                else:
                    current_ids = set()
            else:
                # Skip unknown content types to avoid accidental deletion
                logger.warning(
                    f"Skipping cleanup for unknown content type: {content_type}"
                )
                results_by_type[content_type.value] = {
                    "deleted": 0,
                    "error": "Unknown content type - skipped for safety",
                }
                continue

            # Get all embedding IDs from database
            db_embeddings = await query_raw_with_schema(
                """
                SELECT "contentId"
                FROM {schema_prefix}"UnifiedContentEmbedding"
                WHERE "contentType" = $1::{schema_prefix}"ContentType"
                """,
                content_type,
            )

            db_ids = {row["contentId"] for row in db_embeddings}

            # Find orphaned embeddings (in DB but not in current content)
            orphaned_ids = db_ids - current_ids

            if not orphaned_ids:
                logger.info(f"{content_type.value}: No orphaned embeddings found")
                results_by_type[content_type.value] = {
                    "deleted": 0,
                    "message": "No orphaned embeddings",
                }
                continue

            # Delete orphaned embeddings in batch for better performance
            orphaned_list = list(orphaned_ids)
            try:
                await execute_raw_with_schema(
                    """
                    DELETE FROM {schema_prefix}"UnifiedContentEmbedding"
                    WHERE "contentType" = $1::{schema_prefix}"ContentType"
                      AND "contentId" = ANY($2::text[])
                    """,
                    content_type,
                    orphaned_list,
                )
                deleted = len(orphaned_list)
            except Exception as e:
                logger.error(f"Failed to batch delete orphaned embeddings: {e}")
                deleted = 0

            logger.info(
                f"{content_type.value}: Deleted {deleted}/{len(orphaned_ids)} orphaned embeddings"
            )
            results_by_type[content_type.value] = {
                "deleted": deleted,
                "orphaned": len(orphaned_ids),
                "message": f"Deleted {deleted} orphaned embeddings",
            }

            total_deleted += deleted

        except Exception as e:
            logger.error(f"Failed to cleanup {content_type.value}: {e}")
            results_by_type[content_type.value] = {
                "deleted": 0,
                "error": str(e),
            }

    return {
        "by_type": results_by_type,
        "totals": {
            "deleted": total_deleted,
            "message": f"Deleted {total_deleted} orphaned embeddings",
        },
    }