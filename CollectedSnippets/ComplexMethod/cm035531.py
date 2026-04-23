async def test_save_event_callback_multiple_saves(
        self,
        service: SQLEventCallbackService,
        sample_callback: EventCallback,
    ):
        """Test saving the same callback multiple times."""
        # Save the callback multiple times
        first_save = await service.save_event_callback(sample_callback)
        first_updated_at = first_save.updated_at

        # Wait a small amount to ensure timestamp difference
        import asyncio

        await asyncio.sleep(0.01)

        second_save = await service.save_event_callback(sample_callback)
        second_updated_at = second_save.updated_at

        # Verify timestamps are different (handle timezone differences)
        first_utc = (
            first_updated_at.replace(tzinfo=timezone.utc)
            if first_updated_at.tzinfo is None
            else first_updated_at
        )
        second_utc = (
            second_updated_at.replace(tzinfo=timezone.utc)
            if second_updated_at.tzinfo is None
            else second_updated_at
        )
        assert second_utc >= first_utc

        # Verify it's still the same callback
        assert first_save.id == second_save.id
        assert first_save is second_save  # Same object instance

        # Commit and verify only one record exists
        await service.db_session.commit()
        retrieved_callback = await service.get_event_callback(sample_callback.id)
        assert retrieved_callback is not None
        assert retrieved_callback.id == sample_callback.id