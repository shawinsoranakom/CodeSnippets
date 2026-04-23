async def test_batch_get_conversation_info(
        self,
        service: SQLAppConversationInfoService,
        multiple_conversation_infos: list[AppConversationInfo],
    ):
        """Test batch get operations."""
        # Save all conversation infos
        for info in multiple_conversation_infos:
            await service.save_app_conversation_info(info)

        # Get all IDs
        all_ids = [info.id for info in multiple_conversation_infos]

        # Add a non-existent ID
        nonexistent_id = uuid4()
        all_ids.append(nonexistent_id)

        # Batch get
        results = await service.batch_get_app_conversation_info(all_ids)

        # Verify results
        assert len(results) == len(all_ids)

        # Check that all existing conversations are returned
        for i, original_info in enumerate(multiple_conversation_infos):
            result = results[i]
            assert result is not None
            assert result.id == original_info.id
            assert result.title == original_info.title

        # Check that non-existent conversation returns None
        assert results[-1] is None