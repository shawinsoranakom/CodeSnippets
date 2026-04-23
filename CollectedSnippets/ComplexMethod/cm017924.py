def test_receipt_full_output(self, markitdown):
        """Test complete output for RECEIPT retail purchase PDF."""
        pdf_path = os.path.join(
            TEST_FILES_DIR, "RECEIPT-2024-TXN-98765_retail_purchase.pdf"
        )
        expected_path = os.path.join(
            TEST_FILES_DIR,
            "expected_outputs",
            "RECEIPT-2024-TXN-98765_retail_purchase.md",
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

        # Validate critical sections
        for section in [
            "TECHMART ELECTRONICS",
            "TXN-98765-2024",
            "Sarah Mitchell",
            "$821.14",
            "RETURN POLICY",
        ]:
            assert section in actual_output, f"Missing section: {section}"