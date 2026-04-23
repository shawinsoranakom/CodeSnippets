def test_markdown_table_columns_have_pipes(self, markitdown):
        """Test that form-style PDF columns are separated with pipes."""
        pdf_path = os.path.join(
            TEST_FILES_DIR, "SPARSE-2024-INV-1234_borderless_table.pdf"
        )

        if not os.path.exists(pdf_path):
            pytest.skip(f"Test file not found: {pdf_path}")

        result = markitdown.convert(pdf_path)
        text_content = result.text_content

        # Find table rows and verify column structure
        lines = text_content.split("\n")
        table_rows = [
            line for line in lines if line.startswith("|") and line.endswith("|")
        ]

        assert len(table_rows) > 0, "Should have markdown table rows"

        # Check that at least some rows have multiple columns (pipes)
        multi_col_rows = [row for row in table_rows if row.count("|") >= 3]
        assert (
            len(multi_col_rows) > 5
        ), f"Should have rows with multiple columns, found {len(multi_col_rows)}"