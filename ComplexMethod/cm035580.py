async def test_export_conversation_success(self):
        """Test successful download of conversation trajectory."""
        # Arrange
        conversation_id = uuid4()

        # Mock conversation info
        mock_conversation_info = Mock(spec=AppConversationInfo)
        mock_conversation_info.id = conversation_id
        mock_conversation_info.title = 'Test Conversation'
        mock_conversation_info.created_at = datetime(2024, 1, 1, 12, 0, 0)
        mock_conversation_info.updated_at = datetime(2024, 1, 1, 13, 0, 0)
        mock_conversation_info.selected_repository = 'test/repo'
        mock_conversation_info.git_provider = 'github'
        mock_conversation_info.selected_branch = 'main'
        mock_conversation_info.model_dump_json = Mock(
            return_value='{"id": "test", "title": "Test Conversation"}'
        )

        self.mock_app_conversation_info_service.get_app_conversation_info = AsyncMock(
            return_value=mock_conversation_info
        )

        # Mock events
        mock_event1 = Mock(spec=Event)
        mock_event1.id = uuid4()
        mock_event1.model_dump = Mock(
            return_value={'id': str(mock_event1.id), 'type': 'action'}
        )

        mock_event2 = Mock(spec=Event)
        mock_event2.id = uuid4()
        mock_event2.model_dump = Mock(
            return_value={'id': str(mock_event2.id), 'type': 'observation'}
        )

        # Mock event service search_events to return paginated results
        mock_event_page1 = Mock()
        mock_event_page1.items = [mock_event1]
        mock_event_page1.next_page_id = 'page2'

        mock_event_page2 = Mock()
        mock_event_page2.items = [mock_event2]
        mock_event_page2.next_page_id = None

        self.mock_event_service.search_events = AsyncMock(
            side_effect=[mock_event_page1, mock_event_page2]
        )

        # Act
        result = await self.service.export_conversation(conversation_id)

        # Assert
        assert result is not None
        assert isinstance(result, bytes)  # Should be bytes

        # Verify the zip file contents
        with zipfile.ZipFile(io.BytesIO(result), 'r') as zipf:
            file_list = zipf.namelist()

            # Should contain meta.json and event files
            assert 'meta.json' in file_list
            assert any(
                f.startswith('event_') and f.endswith('.json') for f in file_list
            )

            # Check meta.json content
            with zipf.open('meta.json') as meta_file:
                meta_content = meta_file.read().decode('utf-8')
                assert '"id": "test"' in meta_content
                assert '"title": "Test Conversation"' in meta_content

            # Check event files
            event_files = [f for f in file_list if f.startswith('event_')]
            assert len(event_files) == 2  # Should have 2 event files

            # Verify event file content
            with zipf.open(event_files[0]) as event_file:
                event_content = json.loads(event_file.read().decode('utf-8'))
                assert 'id' in event_content
                assert 'type' in event_content

        # Verify service calls
        self.mock_app_conversation_info_service.get_app_conversation_info.assert_called_once_with(
            conversation_id
        )
        assert self.mock_event_service.search_events.call_count == 2
        mock_conversation_info.model_dump_json.assert_called_once_with(indent=2)