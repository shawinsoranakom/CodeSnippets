async def test_save_event_callback_with_null_values(
        self,
        service: SQLEventCallbackService,
        sample_processor: EventCallbackProcessor,
    ):
        """Test saving a callback with null conversation_id and event_kind."""
        # Create a callback with null values
        callback = EventCallback(
            conversation_id=None,
            processor=sample_processor,
            event_kind=None,
        )

        # Save the callback
        saved_callback = await service.save_event_callback(callback)

        # Verify the callback was saved correctly
        assert saved_callback.id == callback.id
        assert saved_callback.conversation_id is None
        assert saved_callback.event_kind is None
        assert saved_callback.processor == sample_processor

        # Commit and verify persistence
        await service.db_session.commit()
        retrieved_callback = await service.get_event_callback(callback.id)
        assert retrieved_callback is not None
        assert retrieved_callback.conversation_id is None
        assert retrieved_callback.event_kind is None