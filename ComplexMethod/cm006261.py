def downgrade() -> None:
    """Add back the single unique constraint on name column."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Check if file table exists
    table_names = inspector.get_table_names()
    if "file" not in table_names:
        logger.info("file table does not exist, skipping downgrade")
        return

    db_dialect = conn.dialect.name

    try:
        # Pre-check for duplicates that would violate UNIQUE(name)
        dup = conn.execute(sa.text("SELECT name FROM file GROUP BY name HAVING COUNT(*) > 1 LIMIT 1")).first()
        if dup:
            raise RuntimeError(
                "Downgrade aborted: duplicates in file.name would violate UNIQUE(name). "
                "Deduplicate before downgrading."
            )
        if db_dialect == "sqlite":
            # Add the same column validation as upgrade
            res = conn.execute(sa.text('PRAGMA table_info("file")'))
            cols = [row[1] for row in res]
            expected = ['id', 'user_id', 'name', 'path', 'size', 'provider', 'created_at', 'updated_at']
            if set(cols) != set(expected):
                raise RuntimeError(f"SQLite: Unexpected columns on file table: {cols}. Aborting downgrade.")
            # SQLite: Recreate table with both constraints
            logger.info("SQLite: Recreating table with both constraints")

            op.execute("""
                CREATE TABLE file_new (
                    id CHAR(32) NOT NULL, 
                    user_id CHAR(32) NOT NULL, 
                    name VARCHAR NOT NULL, 
                    path VARCHAR NOT NULL, 
                    size INTEGER NOT NULL, 
                    provider VARCHAR, 
                    created_at DATETIME NOT NULL, 
                    updated_at DATETIME NOT NULL, 
                    PRIMARY KEY (id), 
                    CONSTRAINT file_name_user_id_key UNIQUE (name, user_id), 
                    FOREIGN KEY(user_id) REFERENCES user (id),
                    UNIQUE (name)
                )
            """)

            # Copy data
            op.execute("""
                INSERT INTO file_new (id, user_id, name, path, size, provider, created_at, updated_at)
                SELECT id, user_id, name, path, size, provider, created_at, updated_at
                FROM file
            """)

            # Replace table
            op.execute("PRAGMA foreign_keys=OFF")
            try:
                op.execute("DROP TABLE file")
                op.execute("ALTER TABLE file_new RENAME TO file")
            finally:
                op.execute("PRAGMA foreign_keys=ON")

            logger.info("SQLite: Restored single unique constraint on name column")

        elif db_dialect == "postgresql":
            # PostgreSQL: Add constraint back
            schema = sa.inspect(conn).default_schema_name or "public"
            op.create_unique_constraint("file_name_unique", "file", ["name"], schema=schema)
            logger.info("PostgreSQL: Added back single unique constraint on 'name' column")

        else:
            logger.info(f"Downgrade not supported for dialect: {db_dialect}")

    except Exception as e:
        logger.error(f"Error during downgrade: {e}")
        if "constraint" not in str(e).lower():
            raise