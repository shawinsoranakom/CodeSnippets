def reset_db(self, recreate_tables: bool = True) -> Response:
        """
        Reset the database by dropping all tables and optionally recreating them.

        Args:
            recreate_tables (bool): If True, recreates the tables after dropping them.
                                Set to False if you want to call create_db_and_tables() separately.
        """
        if not self._init_lock.acquire(blocking=False):
            logger.warning("Database reset already in progress")
            return Response(message="Database reset already in progress", status=False, data=None)

        try:
            # Dispose existing connections
            self.engine.dispose()
            with Session(self.engine) as session:
                try:
                    # Disable foreign key checks for SQLite
                    if "sqlite" in str(self.engine.url):
                        session.exec(text("PRAGMA foreign_keys=OFF"))  # type: ignore

                    # Drop all tables
                    SQLModel.metadata.drop_all(self.engine)
                    logger.info("All tables dropped successfully")

                    # Re-enable foreign key checks for SQLite
                    if "sqlite" in str(self.engine.url):
                        session.exec(text("PRAGMA foreign_keys=ON"))  # type: ignore

                    session.commit()

                except Exception as e:
                    session.rollback()
                    raise e
                finally:
                    session.close()
                    self._init_lock.release()

            if recreate_tables:
                logger.info("Recreating tables...")
                self.initialize_database(auto_upgrade=False, force_init_alembic=True)

            return Response(
                message="Database reset successfully" if recreate_tables else "Database tables dropped successfully",
                status=True,
                data=None,
            )

        except Exception as e:
            error_msg = f"Error while resetting database: {str(e)}"
            logger.error(error_msg)
            return Response(message=error_msg, status=False, data=None)
        finally:
            if self._init_lock.locked():
                self._init_lock.release()
                logger.info("Database reset lock released")