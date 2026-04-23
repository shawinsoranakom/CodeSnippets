async def test_create_and_get_callback(
        self,
        service: SQLEventCallbackService,
        sample_request: CreateEventCallbackRequest,
    ):
        """Test creating and retrieving a single callback."""
        # Create the callback
        created_callback = await service.create_event_callback(sample_request)

        # Verify the callback was created correctly
        assert created_callback.id is not None
        assert created_callback.conversation_id == sample_request.conversation_id
        assert created_callback.processor == sample_request.processor
        assert created_callback.event_kind == sample_request.event_kind
        assert created_callback.created_at is not None

        # Retrieve the callback
        retrieved_callback = await service.get_event_callback(created_callback.id)

        # Verify the retrieved callback matches
        assert retrieved_callback is not None
        assert retrieved_callback.id == created_callback.id
        assert retrieved_callback.conversation_id == created_callback.conversation_id
        assert retrieved_callback.event_kind == created_callback.event_kind