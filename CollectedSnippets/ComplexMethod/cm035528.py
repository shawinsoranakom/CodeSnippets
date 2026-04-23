async def test_save_event_callback_new(
        self,
        service: SQLEventCallbackService,
        sample_callback: EventCallback,
    ):
        """Test saving a new event callback (insert scenario)."""
        # Save the callback
        original_updated_at = sample_callback.updated_at
        saved_callback = await service.save_event_callback(sample_callback)

        # Verify the returned callback
        assert saved_callback.id == sample_callback.id
        assert saved_callback.conversation_id == sample_callback.conversation_id
        assert saved_callback.processor == sample_callback.processor
        assert saved_callback.event_kind == sample_callback.event_kind
        assert saved_callback.status == sample_callback.status

        # Verify updated_at was changed (handle timezone differences)
        # Convert both to UTC for comparison if needed
        original_utc = (
            original_updated_at.replace(tzinfo=timezone.utc)
            if original_updated_at.tzinfo is None
            else original_updated_at
        )
        saved_utc = (
            saved_callback.updated_at.replace(tzinfo=timezone.utc)
            if saved_callback.updated_at.tzinfo is None
            else saved_callback.updated_at
        )
        assert saved_utc >= original_utc

        # Commit the transaction to persist changes
        await service.db_session.commit()

        # Verify the callback can be retrieved
        retrieved_callback = await service.get_event_callback(sample_callback.id)
        assert retrieved_callback is not None
        assert retrieved_callback.id == sample_callback.id
        assert retrieved_callback.conversation_id == sample_callback.conversation_id
        assert retrieved_callback.event_kind == sample_callback.event_kind