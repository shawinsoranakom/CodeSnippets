async def test_save_event_callback_update_existing(
        self,
        service: SQLEventCallbackService,
        sample_request: CreateEventCallbackRequest,
    ):
        """Test saving an existing event callback (update scenario)."""
        # First create a callback through the service
        created_callback = await service.create_event_callback(sample_request)
        original_updated_at = created_callback.updated_at

        # Modify the callback
        created_callback.event_kind = 'ObservationEvent'
        from openhands.app_server.event_callback.event_callback_models import (
            EventCallbackStatus,
        )

        created_callback.status = EventCallbackStatus.DISABLED

        # Save the modified callback
        saved_callback = await service.save_event_callback(created_callback)

        # Verify the returned callback has the modifications
        assert saved_callback.id == created_callback.id
        assert saved_callback.event_kind == 'ObservationEvent'
        assert saved_callback.status == EventCallbackStatus.DISABLED

        # Verify updated_at was changed (handle timezone differences)
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

        # Verify the changes were persisted
        retrieved_callback = await service.get_event_callback(created_callback.id)
        assert retrieved_callback is not None
        assert retrieved_callback.event_kind == 'ObservationEvent'
        assert retrieved_callback.status == EventCallbackStatus.DISABLED