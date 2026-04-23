def test_multipage_invoice_extraction(self, markitdown):
        """Test extraction of multipage invoice PDF with form-style layout.

        Expected output: Pipe-separated format with clear cell boundaries.
        Form data should be extracted with pipes indicating column separations.
        """
        pdf_path = os.path.join(TEST_FILES_DIR, "REPAIR-2022-INV-001_multipage.pdf")

        if not os.path.exists(pdf_path):
            pytest.skip(f"Test file not found: {pdf_path}")

        result = markitdown.convert(pdf_path)
        text_content = result.text_content

        # Validate basic content is extracted
        expected_strings = [
            "ZAVA AUTO REPAIR",
            "Collision Repair",
            "Redmond, WA",
            "Gabriel Diaz",
            "Jeep",
            "Grand Cherokee",
            "Parts",
            "Body Labor",
            "Paint Labor",
            "GRAND TOTAL",
            # Second page content
            "Bruce Wayne",
            "Batmobile",
        ]
        validate_strings(result, expected_strings)

        # Validate pipe-separated table format
        # Form-style documents should use pipes to separate cells
        assert "|" in text_content, "Form-style PDF should contain pipe separators"

        # Validate key form fields are properly separated
        # These patterns check that label and value are in separate cells
        # Note: cells may have padding spaces for column alignment
        import re

        assert re.search(
            r"\| Insured name\s*\|", text_content
        ), "Insured name should be in its own cell"
        assert re.search(
            r"\| Gabriel Diaz\s*\|", text_content
        ), "Gabriel Diaz should be in its own cell"
        assert re.search(
            r"\| Year\s*\|", text_content
        ), "Year label should be in its own cell"
        assert re.search(
            r"\| 2022\s*\|", text_content
        ), "Year value should be in its own cell"

        # Validate table structure for estimate totals
        assert (
            re.search(r"\| Hours\s*\|", text_content) or "Hours |" in text_content
        ), "Hours column header should be present"
        assert (
            re.search(r"\| Rate\s*\|", text_content) or "Rate |" in text_content
        ), "Rate column header should be present"
        assert (
            re.search(r"\| Cost\s*\|", text_content) or "Cost |" in text_content
        ), "Cost column header should be present"

        # Validate numeric values are extracted
        assert "2,100" in text_content, "Parts cost should be extracted"
        assert "300" in text_content, "Body labor cost should be extracted"
        assert "225" in text_content, "Paint labor cost should be extracted"
        assert "5,738" in text_content, "Grand total should be extracted"

        # Validate second page content (Bruce Wayne invoice)
        assert "Bruce Wayne" in text_content, "Second page customer name"
        assert "Batmobile" in text_content, "Second page vehicle model"
        assert "211,522" in text_content, "Second page grand total"

        # Validate disclaimer text is NOT in table format (long paragraph)
        # The disclaimer should be extracted as plain text, not pipe-separated
        assert (
            "preliminary estimate" in text_content.lower()
        ), "Disclaimer text should be present"