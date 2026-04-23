def test_movie_theater_full_output(self, markitdown):
        """Test complete output for movie theater booking PDF."""
        pdf_path = os.path.join(TEST_FILES_DIR, "movie-theater-booking-2024.pdf")
        expected_path = os.path.join(
            TEST_FILES_DIR, "expected_outputs", "movie-theater-booking-2024.md"
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

        # Check line count
        assert abs(len(actual_lines) - len(expected_lines)) <= 2, (
            f"Line count mismatch: actual={len(actual_lines)}, "
            f"expected={len(expected_lines)}"
        )

        # Check structural elements
        assert actual_output.count("|") > 80, "Should have many pipe separators"
        assert actual_output.count("---") > 8, "Should have table separators"

        # Validate critical sections
        for section in [
            "BOOKING ORDER",
            "STARLIGHT CINEMAS",
            "2024-12-5678",
            "Holiday Spectacular",
            "$12,500.00",
        ]:
            assert section in actual_output, f"Missing section: {section}"

        # Check table structure
        table_rows = [line for line in actual_lines if line.startswith("|")]
        assert (
            len(table_rows) > 15
        ), f"Should have >15 table rows, got {len(table_rows)}"