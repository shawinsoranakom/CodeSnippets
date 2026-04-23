async def _execute(
        self,
        user_id: str | None,
        session: ChatSession,
        **kwargs,
    ) -> ToolResponseBase:
        """
        Capture and store business understanding incrementally.

        Each call merges new data with existing understanding:
        - String fields are overwritten if provided
        - List fields are appended (with deduplication)

        Note: This tool accepts **kwargs because its parameters are derived
        dynamically from the BusinessUnderstandingInput model schema.
        """
        session_id = session.session_id

        if not user_id:
            return ErrorResponse(
                message="Authentication required to save business understanding.",
                session_id=session_id,
            )

        # Build input model from kwargs (only include fields defined in the model)
        valid_fields = set(BusinessUnderstandingInput.model_fields.keys())
        filtered = {k: v for k, v in kwargs.items() if k in valid_fields}

        # Check if any data was provided
        if not any(v is not None for v in filtered.values()):
            return ErrorResponse(
                message="Please provide at least one field to update.",
                session_id=session_id,
            )

        input_data = BusinessUnderstandingInput(**filtered)

        # Track which fields were updated
        updated_fields = [k for k, v in filtered.items() if v is not None]

        # Upsert with merge
        understanding = await understanding_db().upsert_business_understanding(
            user_id, input_data
        )

        # Build current understanding summary (filter out empty values)
        current_understanding = {
            k: v
            for k, v in understanding.model_dump(
                exclude={"id", "user_id", "created_at", "updated_at"}
            ).items()
            if v is not None and v != [] and v != ""
        }

        return UnderstandingUpdatedResponse(
            message=f"Updated understanding with: {', '.join(updated_fields)}. "
            "I now have a better picture of your business context.",
            session_id=session_id,
            updated_fields=updated_fields,
            current_understanding=current_understanding,
        )