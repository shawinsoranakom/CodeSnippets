async def get_variable(self, name: str, field: str, session):
        """Returns the variable for the current user with the specified name.

        Raises:
            ValueError: If the user id is not set and variable not found in context.

        Returns:
            The variable for the current user with the specified name.
        """
        # Check graph context for request-level variable overrides first
        # This allows run_flow to work without user_id when variables are passed
        if hasattr(self, "graph") and self.graph and hasattr(self.graph, "context"):
            context = self.graph.context
            if context and "request_variables" in context:
                request_variables = context["request_variables"]
                if name in request_variables:
                    logger.debug(f"Found context override for variable '{name}'")
                    return request_variables[name]

        # Only check user_id when we need to access the database
        if hasattr(self, "_user_id") and not self.user_id:
            msg = f"User id is not set for {self.__class__.__name__}"
            raise ValueError(msg)

        variable_service = get_variable_service()  # Get service instance
        # Retrieve and decrypt the variable by name for the current user
        if isinstance(self.user_id, str):
            user_id = uuid.UUID(self.user_id)
        elif isinstance(self.user_id, uuid.UUID):
            user_id = self.user_id
        else:
            msg = f"Invalid user id: {self.user_id}"
            raise TypeError(msg)
        return await variable_service.get_variable(user_id=user_id, name=name, field=field, session=session)