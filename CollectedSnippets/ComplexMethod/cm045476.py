def initialize_database(self, auto_upgrade: bool = False, force_init_alembic: bool = True) -> Response:
        """
        Initialize database and migrations in the correct order.

        Args:
            auto_upgrade: If True, automatically generate and apply migrations for schema changes
            force_init_alembic: If True, reinitialize alembic configuration even if it exists
        """
        if not self._init_lock.acquire(blocking=False):
            return Response(message="Database initialization already in progress", status=False)

        try:
            # Enable foreign key constraints for SQLite
            if "sqlite" in str(self.engine.url):
                with self.engine.connect() as conn:
                    conn.execute(text("PRAGMA foreign_keys=ON"))
            inspector = inspect(self.engine)
            tables_exist = inspector.get_table_names()
            if not tables_exist:
                logger.info("Creating database tables...")
                SQLModel.metadata.create_all(self.engine)

                if self.schema_manager.initialize_migrations(force=force_init_alembic):
                    return Response(message="Database initialized successfully", status=True)
                return Response(message="Failed to initialize migrations", status=False)

            # Handle existing database
            if auto_upgrade:
                logger.info("Checking database schema...")
                if self.schema_manager.ensure_schema_up_to_date():
                    return Response(message="Database schema is up to date", status=True)
                return Response(message="Database upgrade failed", status=False)
            elif self._should_auto_upgrade():
                logger.info("Schema changes detected, but auto_upgrade is disabled. Skipping migration check.")
                logger.info("To enable automatic migrations, set auto_upgrade=True")

            return Response(message="Database is ready", status=True)

        except Exception as e:
            error_msg = f"Database initialization failed: {str(e)}"
            logger.error(error_msg)
            return Response(message=error_msg, status=False)
        finally:
            self._init_lock.release()