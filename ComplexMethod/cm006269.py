def _handle_duplicates_before_upgrade(conn) -> None:
    """
    Ensure (user_id, name) is unique by renaming older duplicates before adding the composite unique constraint.
    Keeps the most recently updated/created/id-highest record; renames the rest with _N suffix.
    """
    logger.info("Scanning for duplicate file names per user...")
    duplicates = conn.execute(
        sa.text(
            """
            SELECT user_id, name, COUNT(*) AS cnt
            FROM file
            GROUP BY user_id, name
            HAVING COUNT(*) > 1
            """
        )
    ).fetchall()

    if not duplicates:
        logger.info("No duplicates found.")
        return

    logger.info("Found %d duplicate sets. Resolving...", len(duplicates))

    # Add progress indicator for large datasets
    if len(duplicates) > 100:
        logger.info("Large number of duplicates detected. This may take several minutes...")

    # Wrap in a nested transaction so we fail cleanly on any error
    with conn.begin_nested():
        # Process duplicates in batches for better performance on large datasets
        for batch_start in range(0, len(duplicates), BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, len(duplicates))
            batch = duplicates[batch_start:batch_end]

            if len(duplicates) > BATCH_SIZE:
                logger.info("Processing batch %d-%d of %d duplicate sets...", 
                           batch_start + 1, batch_end, len(duplicates))

            for user_id, name, cnt in batch:
                logger.debug("Resolving duplicates for user=%s, name=%r (count=%s)", user_id, name, cnt)

                file_ids = conn.execute(
                    sa.text(
                        """
                        SELECT id
                        FROM file
                        WHERE user_id = :uid AND name = :name
                        ORDER BY updated_at DESC, created_at DESC, id DESC
                        """
                    ),
                    {"uid": user_id, "name": name},
                ).scalars().all()

                # Keep the first (most recent), rename the rest
                for file_id in file_ids[1:]:
                    new_name = _next_available_name(conn, user_id, name)
                    conn.execute(
                        sa.text("UPDATE file SET name = :new_name WHERE id = :fid"),
                        {"new_name": new_name, "fid": file_id},
                    )
                    logger.debug("Renamed id=%s: %r -> %r", file_id, name, new_name)

            # Progress update for large batches
            if len(duplicates) > BATCH_SIZE and batch_end < len(duplicates):
                logger.info("Completed %d of %d duplicate sets (%.1f%%)", 
                           batch_end, len(duplicates), (batch_end / len(duplicates)) * 100)

    logger.info("Duplicate resolution completed.")