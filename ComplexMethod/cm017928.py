def test_multipage_invoice_table_structure(self, markitdown):
        """Test that multipage invoice PDF has pipe-separated format."""
        pdf_path = os.path.join(TEST_FILES_DIR, "REPAIR-2022-INV-001_multipage.pdf")

        if not os.path.exists(pdf_path):
            pytest.skip(f"Test file not found: {pdf_path}")

        result = markitdown.convert(pdf_path)
        text_content = result.text_content

        # Should have pipe-separated content
        assert "|" in text_content, "Invoice PDF should have pipe separators"

        # Find rows with pipes
        lines = text_content.split("\n")
        pipe_rows = [
            line for line in lines if line.startswith("|") and line.endswith("|")
        ]

        assert (
            len(pipe_rows) > 10
        ), f"Should have multiple pipe-separated rows, found {len(pipe_rows)}"

        # Check that some rows have multiple columns
        multi_col_rows = [row for row in pipe_rows if row.count("|") >= 4]
        assert len(multi_col_rows) > 5, "Should have rows with 3+ columns"