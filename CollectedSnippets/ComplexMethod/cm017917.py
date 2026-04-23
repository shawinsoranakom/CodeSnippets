def test_borderless_table_correct_position(self, markitdown):
        """Test that tables appear in correct positions relative to text."""
        pdf_path = os.path.join(
            TEST_FILES_DIR, "SPARSE-2024-INV-1234_borderless_table.pdf"
        )

        if not os.path.exists(pdf_path):
            pytest.skip(f"Test file not found: {pdf_path}")

        result = markitdown.convert(pdf_path)
        text_content = result.text_content

        # Verify content order - header should come before table content, which should come before analysis
        header_pos = text_content.find("Prepared By: Sarah Martinez")
        # Look for Product Code in any pipe-separated format
        product_code_pos = text_content.find("Product Code")
        variance_pos = text_content.find("Variance Analysis:")

        assert header_pos != -1, "Header should be found"
        assert product_code_pos != -1, "Product Code should be found"
        assert variance_pos != -1, "Variance Analysis should be found"

        assert (
            header_pos < product_code_pos < variance_pos
        ), "Product data should appear between header and Variance Analysis"

        # Second table content should appear after "Extended Inventory Review"
        extended_review_pos = text_content.find("Extended Inventory Review:")
        # Look for Category header which is in second table
        category_pos = text_content.find("Category")
        recommendations_pos = text_content.find("Recommendations:")

        if (
            extended_review_pos != -1
            and category_pos != -1
            and recommendations_pos != -1
        ):
            # Find Category position after Extended Inventory Review
            category_after_review = text_content.find("Category", extended_review_pos)
            if category_after_review != -1:
                assert (
                    extended_review_pos < category_after_review < recommendations_pos
                ), "Extended review table should appear between Extended Inventory Review and Recommendations"