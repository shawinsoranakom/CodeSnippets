def test_academic_pdf_extraction(self, markitdown):
        """Test extraction of academic paper PDF (scientific document).

        Expected output: Plain text without tables or pipe characters.
        Scientific documents should be extracted as flowing text with proper spacing,
        not misinterpreted as tables.
        """
        pdf_path = os.path.join(TEST_FILES_DIR, "test.pdf")

        if not os.path.exists(pdf_path):
            pytest.skip(f"Test file not found: {pdf_path}")

        result = markitdown.convert(pdf_path)
        text_content = result.text_content

        # Validate academic paper content with proper spacing
        expected_strings = [
            "Introduction",
            "Large language models",  # Should have proper spacing, not "Largelanguagemodels"
            "agents",
            "multi-agent",  # Should be properly hyphenated
        ]
        validate_strings(result, expected_strings)

        # Validate proper text formatting (words separated by spaces)
        assert "LLMs" in text_content, "Should contain 'LLMs' acronym"
        assert "reasoning" in text_content, "Should contain 'reasoning'"
        assert "observations" in text_content, "Should contain 'observations'"

        # Ensure content is not empty and has proper length
        assert len(text_content) > 1000, "Academic PDF should have substantial content"

        # Scientific documents should NOT have tables or pipe characters
        assert (
            "|" not in text_content
        ), "Scientific document should not contain pipe characters (no tables)"

        # Verify no markdown tables were extracted
        tables = extract_markdown_tables(text_content)
        assert (
            len(tables) == 0
        ), f"Scientific document should have no tables, found {len(tables)}"

        # Verify text is properly formatted with spaces between words
        # Check that common phrases are NOT joined together (which would indicate bad extraction)
        assert (
            "Largelanguagemodels" not in text_content
        ), "Text should have proper spacing, not joined words"
        assert (
            "multiagentconversations" not in text_content.lower()
        ), "Text should have proper spacing between words"