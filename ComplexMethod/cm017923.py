def test_repair_multipage_full_output(self, markitdown):
        """Test complete output for REPAIR multipage invoice PDF."""
        pdf_path = os.path.join(TEST_FILES_DIR, "REPAIR-2022-INV-001_multipage.pdf")
        expected_path = os.path.join(
            TEST_FILES_DIR, "expected_outputs", "REPAIR-2022-INV-001_multipage.md"
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
        assert actual_output.count("|") > 40, "Should have many pipe separators"

        # Validate critical sections
        for section in [
            "ZAVA AUTO REPAIR",
            "Gabriel Diaz",
            "Jeep",
            "Grand Cherokee",
            "GRAND TOTAL",
        ]:
            assert section in actual_output, f"Missing section: {section}"