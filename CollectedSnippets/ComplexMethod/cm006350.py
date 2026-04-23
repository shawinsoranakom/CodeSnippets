def _create_db_and_tables(connection) -> None:
        from sqlalchemy import inspect

        inspector = inspect(connection)
        table_names = inspector.get_table_names()
        current_tables = [
            "flow",
            "user",
            "apikey",
            "folder",
            "message",
            "variable",
            "transaction",
            "vertex_build",
            "job",
        ]

        if table_names and all(table in table_names for table in current_tables):
            logger.debug("Database and tables already exist")
            return

        logger.debug("Creating database and tables")

        for table in SQLModel.metadata.sorted_tables:
            try:
                table.create(connection, checkfirst=True)
            except OperationalError as oe:
                logger.warning(f"Table {table} already exists, skipping. Exception: {oe}")
            except Exception as exc:
                msg = f"Error creating table {table}"
                logger.exception(msg)
                raise RuntimeError(msg) from exc

        # Now check if the required tables exist, if not, something went wrong.
        inspector = inspect(connection)
        table_names = inspector.get_table_names()
        for table in current_tables:
            if table not in table_names:
                logger.error("Something went wrong creating the database and tables.")
                logger.error("Please check your database settings.")
                msg = "Something went wrong creating the database and tables."
                raise RuntimeError(msg)

        logger.debug("Database and tables created successfully")