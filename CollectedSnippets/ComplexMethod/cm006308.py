async def cleanup_orphaned_records() -> None:
    """Clean up all records that reference non-existent flows."""
    from langflow.services.database.models.flow.model import Flow

    async with session_scope() as session:
        # Create a subquery of existing flow IDs
        flow_ids_subquery = select(Flow.id)

        # Tables that have flow_id foreign keys
        tables: list[type[VertexBuildTable | MessageTable | TransactionTable]] = [
            MessageTable,
            VertexBuildTable,
            TransactionTable,
        ]

        for table in tables:
            try:
                # Get distinct orphaned flow IDs from the table
                orphaned_flow_ids = (
                    await session.exec(
                        select(col(table.flow_id).distinct()).where(col(table.flow_id).not_in(flow_ids_subquery))
                    )
                ).all()

                if orphaned_flow_ids:
                    logger.debug(f"Found {len(orphaned_flow_ids)} orphaned flow IDs in {table.__name__}")

                    # Delete all orphaned records in a single query
                    await session.exec(delete(table).where(col(table.flow_id).in_(orphaned_flow_ids)))

                    # Clean up any associated storage files
                    storage_service: StorageService = get_storage_service()
                    for flow_id in orphaned_flow_ids:
                        try:
                            files = await storage_service.list_files(str(flow_id))
                            for file in files:
                                try:
                                    await storage_service.delete_file(str(flow_id), file)
                                except Exception as exc:  # noqa: BLE001
                                    logger.error(f"Failed to delete file {file} for flow {flow_id}: {exc!s}")
                            # Delete the flow directory after all files are deleted
                            flow_dir = storage_service.data_dir / str(flow_id)
                            if await flow_dir.exists():
                                await flow_dir.rmdir()
                        except Exception as exc:  # noqa: BLE001
                            logger.error(f"Failed to list files for flow {flow_id}: {exc!s}")

                    logger.debug(f"Successfully deleted orphaned records from {table.__name__}")

            except Exception as exc:  # noqa: BLE001
                logger.error(f"Error cleaning up orphaned records in {table.__name__}: {exc!s}")