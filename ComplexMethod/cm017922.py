def test_sparse_borderless_table_full_output(self, markitdown):
        """Test complete output for SPARSE borderless table PDF."""
        pdf_path = os.path.join(
            TEST_FILES_DIR, "SPARSE-2024-INV-1234_borderless_table.pdf"
        )
        expected_path = os.path.join(
            TEST_FILES_DIR,
            "expected_outputs",
            "SPARSE-2024-INV-1234_borderless_table.md",
        )

        if not os.path.exists(pdf_path):
            pytest.skip(f"Test file not found: {pdf_path}")

        if not os.path.exists(expected_path):
            pytest.skip(f"Expected output not found: {expected_path}")

        result = markitdown.convert(pdf_path)
        actual_output = result.text_content

        with open(expected_path, "r", encoding="utf-8") as f:
            expected_output = f.read()

        # Compare outputs
        actual_lines = [line.rstrip() for line in actual_output.split("\n")]
        expected_lines = [line.rstrip() for line in expected_output.split("\n")]

        # Check line count is close
        assert abs(len(actual_lines) - len(expected_lines)) <= 2, (
            f"Line count mismatch: actual={len(actual_lines)}, "
            f"expected={len(expected_lines)}"
        )

        # Check structural elements
        assert actual_output.count("|") > 50, "Should have many pipe separators"

        # Validate critical sections
        for section in [
            "INVENTORY RECONCILIATION REPORT",
            "SPARSE-2024-INV-1234",
            "SKU-8847",
            "SKU-9201",
            "Variance Analysis",
        ]:
            assert section in actual_output, f"Missing section: {section}"