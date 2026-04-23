def test_academic_paper_full_output(self, markitdown):
        """Test complete output for academic paper PDF."""
        pdf_path = os.path.join(TEST_FILES_DIR, "test.pdf")
        expected_path = os.path.join(TEST_FILES_DIR, "expected_outputs", "test.md")

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

        # Academic paper should not have pipe separators
        assert (
            actual_output.count("|") == 0
        ), "Academic paper should not have pipe separators"

        # Validate critical sections
        for section in [
            "Introduction",
            "Large language models",
            "agents",
            "multi-agent",
        ]:
            assert section in actual_output, f"Missing section: {section}"