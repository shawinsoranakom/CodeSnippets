def test_chat_response_with_all_fields(self):
        """Test creating chat response with all fields."""
        files = [{"path": "/test.txt", "name": "test.txt", "type": "txt"}]

        response = ChatOutputResponse(
            message="Test message",
            sender="Human",
            sender_name="User",
            session_id="session-123",
            stream_url="http://stream.url",
            component_id="comp-456",
            files=files,
            type="text",
        )

        assert response.message == "Test message"
        assert response.sender == "Human"
        assert response.sender_name == "User"
        assert response.session_id == "session-123"
        assert response.stream_url == "http://stream.url"
        assert response.component_id == "comp-456"
        assert response.files == files
        assert response.type == "text"