def downgrade() -> None:
    start_time = time.time()
    logger.info("Starting downgrade: reverting to single-column unique on (name)")

    conn = op.get_bind()
    inspector = inspect(conn)

    # 1) Ensure no cross-user duplicates on name (since we'll enforce global uniqueness on name)
    logger.info("Checking for cross-user duplicate names prior to downgrade...")
    validation_start = time.time()

    dup_names = conn.execute(
        sa.text(
            """
            SELECT name, COUNT(*) AS cnt
            FROM file
            GROUP BY name
            HAVING COUNT(*) > 1
            """
        )
    ).fetchall()

    validation_duration = time.time() - validation_start
    if validation_duration > 1.0:  # Only log if it took more than 1 second
        logger.info("Validation completed in %.2f seconds", validation_duration)

    if dup_names:
        examples = [row[0] for row in dup_names[:10]]
        raise RuntimeError(
            "Downgrade aborted: duplicate names exist across users. "
            f"Examples: {examples}{'...' if len(dup_names) > 10 else ''}. "
            "Rename conflicting files before downgrading."
        )

    # 2) Detect constraints
    inspector = inspect(conn)  # refresh
    composite_uc = _get_unique_constraints_by_columns(inspector, "file", {"name", "user_id"})
    single_name_uc = _get_unique_constraints_by_columns(inspector, "file", {"name"})

    # 3) Perform alteration using batch with reflect to preserve other objects
    constraint_start = time.time()
    with op.batch_alter_table("file", recreate="always") as batch_op:
        if composite_uc:
            logger.info("Dropping composite unique: %s", composite_uc)
            batch_op.drop_constraint(composite_uc, type_="unique")
        else:
            logger.info("No composite unique found to drop.")

        if not single_name_uc:
            logger.info("Creating single-column unique: file_name_key on (name)")
            batch_op.create_unique_constraint("file_name_key", ["name"])
        else:
            logger.info("Single-column unique already present: %s", single_name_uc)

    constraint_duration = time.time() - constraint_start
    if constraint_duration > 1.0:  # Only log if it took more than 1 second
        logger.info("Constraint operations completed in %.2f seconds", constraint_duration)

    total_duration = time.time() - start_time
    logger.info("Downgrade completed successfully in %.2f seconds", total_duration)