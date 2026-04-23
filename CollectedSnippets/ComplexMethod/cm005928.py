def test_url_component_multiple_urls(self, mock_recursive_loader):
        """Test URLComponent with multiple URL inputs."""
        # Setup component with multiple URLs
        component = URLComponent()
        urls = ["https://example1.com", "https://example2.com"]
        component.set_attributes({"urls": urls})

        # Create mock documents for each URL
        mock_docs = [
            Mock(
                page_content="Content from first URL",
                metadata={
                    "source": "https://example1.com",
                    "title": "First Page",
                    "description": "First Description",
                    "content_type": "text/html",
                    "language": "en",
                },
            ),
            Mock(
                page_content="Content from second URL",
                metadata={
                    "source": "https://example2.com",
                    "title": "Second Page",
                    "description": "Second Description",
                    "content_type": "text/html",
                    "language": "en",
                },
            ),
        ]

        # Configure mock to return both documents
        mock_recursive_loader.return_value = mock_docs

        # Execute component
        result = component.fetch_content()

        # Verify results
        assert isinstance(result, DataFrame)
        assert len(result) == 4

        # Verify first URL content
        first_row = result.iloc[0]
        assert first_row["text"] == "Content from first URL"
        assert first_row["url"] == "https://example1.com"
        assert first_row["title"] == "First Page"
        assert first_row["description"] == "First Description"

        # Verify second URL content
        second_row = result.iloc[1]
        assert second_row["text"] == "Content from second URL"
        assert second_row["url"] == "https://example2.com"
        assert second_row["title"] == "Second Page"
        assert second_row["description"] == "Second Description"