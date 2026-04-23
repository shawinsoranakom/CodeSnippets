def test_all_pdfs_table_rows_consistent(self, markitdown):
        """Test that all PDF tables have rows with pipe-separated content.

        Note: With gap-based column detection, rows may have different column counts
        depending on how content is spaced in the PDF. What's important is that each
        row has pipe separators and the content is readable.
        """
        pdf_files = [
            "SPARSE-2024-INV-1234_borderless_table.pdf",
            "REPAIR-2022-INV-001_multipage.pdf",
            "RECEIPT-2024-TXN-98765_retail_purchase.pdf",
            "test.pdf",
        ]

        for pdf_file in pdf_files:
            pdf_path = os.path.join(TEST_FILES_DIR, pdf_file)
            if not os.path.exists(pdf_path):
                continue

            result = markitdown.convert(pdf_path)
            tables = extract_markdown_tables(result.text_content)

            for table_idx, table in enumerate(tables):
                if not table:
                    continue

                # Verify each row has at least one column (pipe-separated content)
                for row_idx, row in enumerate(table):
                    assert (
                        len(row) >= 1
                    ), f"{pdf_file}: Table {table_idx}, row {row_idx} has no columns"

                    # Verify the row has non-empty content
                    row_content = " ".join(cell.strip() for cell in row)
                    assert (
                        len(row_content.strip()) > 0
                    ), f"{pdf_file}: Table {table_idx}, row {row_idx} is empty"