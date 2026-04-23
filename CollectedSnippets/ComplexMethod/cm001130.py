def test_web_scraping_content_sanitization(self):
        """Test sanitization of typical web scraping content with null characters."""
        # Simulate web content that might contain null bytes from SearchTheWebBlock
        web_content = "Article title\x00Hidden null\x01Start of heading\x08Backspace\x0CForm feed content\x1FUnit separator\x7FDelete char"

        result = SafeJson(web_content)
        assert isinstance(result, Json)

        # Verify all problematic characters are removed
        sanitized_content = str(result.data)
        assert "\x00" not in sanitized_content
        assert "\x01" not in sanitized_content
        assert "\x08" not in sanitized_content
        assert "\x0C" not in sanitized_content
        assert "\x1F" not in sanitized_content
        assert "\x7F" not in sanitized_content

        # Verify the content is still readable
        assert "Article title" in sanitized_content
        assert "Hidden null" in sanitized_content
        assert "content" in sanitized_content