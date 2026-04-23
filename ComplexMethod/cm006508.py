def format_conflict_detail(
        self,
        raw_message: str,
        *,
        resource: str | None = None,
        resource_name: str | None = None,
    ) -> str:
        normalized_resource_name = str(resource_name or "").strip() or None
        if resource == "tool":
            return (
                f"A tool with name '{normalized_resource_name}' already exists in the provider. "
                "Please choose a different name."
                if normalized_resource_name
                else "A tool with this name already exists in the provider. Please choose a different name."
            )
        if resource == "connection":
            return (
                f"A connection with app_id '{normalized_resource_name}' already exists in the provider. "
                "Please choose a different name."
                if normalized_resource_name
                else "A connection referenced in this request already exists in the provider. "
                "Please choose a different name."
            )
        if resource == "agent":
            return (
                f"An agent with name '{normalized_resource_name}' already exists in the provider. "
                "Please choose a different name."
                if normalized_resource_name
                else "An agent with this name already exists in the provider. Please choose a different name."
            )

        return super().format_conflict_detail(
            raw_message,
            resource=resource,
            resource_name=resource_name,
        )