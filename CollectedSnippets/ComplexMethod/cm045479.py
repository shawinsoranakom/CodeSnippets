def delete(self, model_class: type[BaseDBModel], filters: dict | None = None) -> Response:
        """Delete an entity"""
        status_message = ""
        status = True

        with Session(self.engine) as session:
            try:
                if "sqlite" in str(self.engine.url):
                    session.exec(text("PRAGMA foreign_keys=ON"))  # type: ignore
                statement = select(model_class)  # type: ignore
                if filters:
                    conditions = [getattr(model_class, col) == value for col, value in filters.items()]
                    statement = statement.where(and_(*conditions))

                rows = session.exec(statement).all()

                if rows:
                    for row in rows:
                        session.delete(row)
                    session.commit()
                    status_message = f"{model_class.__name__} Deleted Successfully"
                else:
                    status_message = "Row not found"
                    logger.info(f"Row with filters {filters} not found")

            except exc.IntegrityError as e:
                session.rollback()
                status = False
                status_message = f"Integrity error: The {model_class.__name__} is linked to another entity and cannot be deleted. {e}"
                # Log the specific integrity error
                logger.error(status_message)
            except Exception as e:
                session.rollback()
                status = False
                status_message = f"Error while deleting: {e}"
                logger.error(status_message)

        return Response(message=status_message, status=status, data=None)