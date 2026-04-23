def test_borderless_table_extraction(self, markitdown):
        """Test extraction of borderless tables from SPARSE inventory PDF.

        Expected output structure:
        - Header: INVENTORY RECONCILIATION REPORT with Report ID, Warehouse, Date, Prepared By
        - Pipe-separated rows with inventory data
        - Text section: Variance Analysis with Summary Statistics
        - More pipe-separated rows with extended inventory review
        - Footer: Recommendations section
        """
        pdf_path = os.path.join(
            TEST_FILES_DIR, "SPARSE-2024-INV-1234_borderless_table.pdf"
        )

        if not os.path.exists(pdf_path):
            pytest.skip(f"Test file not found: {pdf_path}")

        result = markitdown.convert(pdf_path)
        text_content = result.text_content

        # Validate document header content
        expected_strings = [
            "INVENTORY RECONCILIATION REPORT",
            "Report ID: SPARSE-2024-INV-1234",
            "Warehouse: Distribution Center East",
            "Report Date: 2024-11-15",
            "Prepared By: Sarah Martinez",
        ]
        validate_strings(result, expected_strings)

        # Validate pipe-separated format is used
        assert "|" in text_content, "Should have pipe separators for form-style data"

        # --- Validate First Table Data (Inventory Variance) ---
        # Validate table headers are present
        first_table_headers = [
            "Product Code",
            "Location",
            "Expected",
            "Actual",
            "Variance",
            "Status",
        ]
        for header in first_table_headers:
            assert header in text_content, f"Should contain header '{header}'"

        # Validate first table has all expected SKUs
        first_table_skus = ["SKU-8847", "SKU-9201", "SKU-4563", "SKU-7728"]
        for sku in first_table_skus:
            assert sku in text_content, f"Should contain {sku}"

        # Validate first table has correct status values
        expected_statuses = ["OK", "CRITICAL"]
        for status in expected_statuses:
            assert status in text_content, f"Should contain status '{status}'"

        # Validate first table has location codes
        expected_locations = ["A-12", "B-07", "C-15", "D-22", "A-08"]
        for loc in expected_locations:
            assert loc in text_content, f"Should contain location '{loc}'"

        # --- Validate Second Table Data (Extended Inventory Review) ---
        # Validate second table headers
        second_table_headers = [
            "Category",
            "Unit Cost",
            "Total Value",
            "Last Audit",
            "Notes",
        ]
        for header in second_table_headers:
            assert header in text_content, f"Should contain header '{header}'"

        # Validate second table has all expected SKUs (10 products)
        second_table_skus = [
            "SKU-8847",
            "SKU-9201",
            "SKU-4563",
            "SKU-7728",
            "SKU-3345",
            "SKU-5512",
            "SKU-6678",
            "SKU-7789",
            "SKU-2234",
            "SKU-1123",
        ]
        for sku in second_table_skus:
            assert sku in text_content, f"Should contain {sku}"

        # Validate second table has categories
        expected_categories = ["Electronics", "Hardware", "Software", "Accessories"]
        for category in expected_categories:
            assert category in text_content, f"Should contain category '{category}'"

        # Validate second table has cost values (spot check)
        expected_costs = ["$45.00", "$32.50", "$120.00", "$15.75"]
        for cost in expected_costs:
            assert cost in text_content, f"Should contain cost '{cost}'"

        # Validate second table has note values
        expected_notes = ["Verified", "Critical", "Pending"]
        for note in expected_notes:
            assert note in text_content, f"Should contain note '{note}'"

        # --- Validate Analysis Text Section ---
        analysis_strings = [
            "Variance Analysis:",
            "Summary Statistics:",
            "Total Variance Cost: $4,287.50",
            "Critical Items: 1",
            "Overall Accuracy: 97.2%",
            "Recommendations:",
        ]
        validate_strings(result, analysis_strings)

        # --- Validate Document Structure Order ---
        # Verify sections appear in correct order
        # Note: Using flexible patterns since column merging may occur based on gap detection
        import re

        header_pos = text_content.find("INVENTORY RECONCILIATION REPORT")
        # Look for Product Code header - may be in same column as Location or separate
        first_table_match = re.search(r"\|\s*Product Code", text_content)
        variance_pos = text_content.find("Variance Analysis:")
        extended_review_pos = text_content.find("Extended Inventory Review:")
        # Second table - look for SKU entries after extended review section
        # The table may not have pipes on every row due to paragraph detection
        second_table_pos = -1
        if extended_review_pos != -1:
            # Look for either "| Product Code" or "Product Code" as table header
            second_table_match = re.search(
                r"Product Code.*Category", text_content[extended_review_pos:]
            )
            if second_table_match:
                # Adjust position to be relative to full text
                second_table_pos = extended_review_pos + second_table_match.start()
        recommendations_pos = text_content.find("Recommendations:")

        positions = {
            "header": header_pos,
            "first_table": first_table_match.start() if first_table_match else -1,
            "variance_analysis": variance_pos,
            "extended_review": extended_review_pos,
            "second_table": second_table_pos,
            "recommendations": recommendations_pos,
        }

        # All sections should be found
        for name, pos in positions.items():
            assert pos != -1, f"Section '{name}' not found in output"

        # Verify correct order
        assert (
            positions["header"] < positions["first_table"]
        ), "Header should come before first table"
        assert (
            positions["first_table"] < positions["variance_analysis"]
        ), "First table should come before Variance Analysis"
        assert (
            positions["variance_analysis"] < positions["extended_review"]
        ), "Variance Analysis should come before Extended Review"
        assert (
            positions["extended_review"] < positions["second_table"]
        ), "Extended Review should come before second table"
        assert (
            positions["second_table"] < positions["recommendations"]
        ), "Second table should come before Recommendations"