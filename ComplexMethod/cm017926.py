def test_markdown_table_has_pipe_format(self, markitdown):
        """Test that form-style PDFs have pipe-separated format."""
        pdf_path = os.path.join(
            TEST_FILES_DIR, "SPARSE-2024-INV-1234_borderless_table.pdf"
        )

        if not os.path.exists(pdf_path):
            pytest.skip(f"Test file not found: {pdf_path}")

        result = markitdown.convert(pdf_path)
        text_content = result.text_content

        # Find rows with pipes
        lines = text_content.split("\n")
        pipe_rows = [
            line for line in lines if line.startswith("|") and line.endswith("|")
        ]

        assert len(pipe_rows) > 0, "Should have pipe-separated rows"

        # Check that Product Code appears in a pipe-separated row
        product_code_found = any("Product Code" in row for row in pipe_rows)
        assert product_code_found, "Product Code should be in pipe-separated format"