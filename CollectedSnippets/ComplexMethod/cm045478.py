def get(
        self,
        model_class: type[BaseDBModel],
        filters: dict | None = None,
        return_json: bool = False,
        order: str = "desc",
    ):
        """List entities"""
        with Session(self.engine) as session:
            result = []
            status = True
            status_message = ""

            try:
                statement = select(model_class)  # type: ignore
                if filters:
                    conditions = [getattr(model_class, col) == value for col, value in filters.items()]
                    statement = statement.where(and_(*conditions))

                if hasattr(model_class, "created_at") and order:
                    order_by_clause = getattr(model_class.created_at, order)()  # Dynamically apply asc/desc
                    statement = statement.order_by(order_by_clause)

                items = session.exec(statement).all()
                result = [self._model_to_dict(item) if return_json else item for item in items]
                status_message = f"{model_class.__name__} Retrieved Successfully"
            except Exception as e:
                session.rollback()
                status = False
                status_message = f"Error while fetching {model_class.__name__}"
                logger.error("Error while getting items: " + str(model_class.__name__) + " " + str(e))

            return Response(message=status_message, status=status, data=result)