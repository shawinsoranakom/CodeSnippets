def test_basic_chat_response_creation(self):
        """Test creating basic chat response."""
        response = ChatOutputResponse(message="Hello, world!", type="text")

        assert response.message == "Hello, world!"
        assert response.sender == "Machine"  # Default value
        assert response.sender_name == "AI"  # Default value
        assert response.type == "text"
        assert response.files == []
        assert response.session_id is None
        assert response.stream_url is None
        assert response.component_id is None