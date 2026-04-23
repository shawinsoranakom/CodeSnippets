async def test_export_conversation_large_pagination(self):
        """Test download with multiple pages of events."""
        # Arrange
        conversation_id = uuid4()

        # Mock conversation info
        mock_conversation_info = Mock(spec=AppConversationInfo)
        mock_conversation_info.id = conversation_id
        mock_conversation_info.title = 'Large Conversation'
        mock_conversation_info.model_dump_json = Mock(
            return_value='{"id": "test", "title": "Large Conversation"}'
        )

        self.mock_app_conversation_info_service.get_app_conversation_info = AsyncMock(
            return_value=mock_conversation_info
        )

        # Create multiple pages of events
        events_per_page = 3
        total_pages = 4
        all_events = []

        for page_num in range(total_pages):
            page_events = []
            for i in range(events_per_page):
                mock_event = Mock(spec=Event)
                mock_event.id = uuid4()
                mock_event.model_dump = Mock(
                    return_value={
                        'id': str(mock_event.id),
                        'type': f'event_page_{page_num}_item_{i}',
                    }
                )
                page_events.append(mock_event)
                all_events.append(mock_event)

            mock_event_page = Mock()
            mock_event_page.items = page_events
            mock_event_page.next_page_id = (
                f'page{page_num + 1}' if page_num < total_pages - 1 else None
            )

            if page_num == 0:
                first_page = mock_event_page
            elif page_num == 1:
                second_page = mock_event_page
            elif page_num == 2:
                third_page = mock_event_page
            else:
                fourth_page = mock_event_page

        self.mock_event_service.search_events = AsyncMock(
            side_effect=[first_page, second_page, third_page, fourth_page]
        )

        # Act
        result = await self.service.export_conversation(conversation_id)

        # Assert
        assert result is not None
        assert isinstance(result, bytes)  # Should be bytes

        # Verify the zip file contents
        with zipfile.ZipFile(io.BytesIO(result), 'r') as zipf:
            file_list = zipf.namelist()

            # Should contain meta.json and all event files
            assert 'meta.json' in file_list
            event_files = [f for f in file_list if f.startswith('event_')]
            assert (
                len(event_files) == total_pages * events_per_page
            )  # Should have all events

        # Verify service calls - should call search_events for each page
        assert self.mock_event_service.search_events.call_count == total_pages