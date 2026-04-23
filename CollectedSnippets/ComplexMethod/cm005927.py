def test_url_component_basic_functionality(self, mock_recursive_loader):
        """Test basic URLComponent functionality."""
        component = URLComponent()
        component.set_attributes({"urls": ["https://example.com"], "max_depth": 2})

        mock_doc = Mock(
            page_content="test content",
            metadata={
                "source": "https://example.com",
                "title": "Test Page",
                "description": "Test Description",
                "content_type": "text/html",
                "language": "en",
            },
        )
        mock_recursive_loader.return_value = [mock_doc]

        data_frame = component.fetch_content()
        assert isinstance(data_frame, DataFrame)
        assert len(data_frame) == 1

        row = data_frame.iloc[0]
        assert row["text"] == "test content"
        assert row["url"] == "https://example.com"
        assert row["title"] == "Test Page"
        assert row["description"] == "Test Description"
        assert row["content_type"] == "text/html"
        assert row["language"] == "en"