def test_receipt_pdf_extraction(self, markitdown):
        """Test extraction of receipt PDF (no tables, formatted text).

        Expected output structure:
        - Store header: TECHMART ELECTRONICS with address
        - Transaction info: Store #, date, TXN, Cashier, Register
        - Line items: 6 products with prices and member discounts
        - Totals: Subtotal, Member Discount, Sales Tax, Rewards, TOTAL
        - Payment info: Visa Card, Auth, Ref
        - Rewards member info: Name, ID, Points
        - Return policy and footer
        """
        pdf_path = os.path.join(
            TEST_FILES_DIR, "RECEIPT-2024-TXN-98765_retail_purchase.pdf"
        )

        if not os.path.exists(pdf_path):
            pytest.skip(f"Test file not found: {pdf_path}")

        result = markitdown.convert(pdf_path)
        text_content = result.text_content

        # --- Validate Store Header ---
        store_header = [
            "TECHMART ELECTRONICS",
            "4567 Innovation Blvd",
            "San Francisco, CA 94103",
            "(415) 555-0199",
        ]
        validate_strings(result, store_header)

        # --- Validate Transaction Info ---
        transaction_info = [
            "Store #0342 - Downtown SF",
            "11/23/2024",
            "TXN: TXN-98765-2024",
            "Cashier: Emily Rodriguez",
            "Register: POS-07",
        ]
        validate_strings(result, transaction_info)

        # --- Validate Line Items (6 products) ---
        line_items = [
            # Product 1: Headphones
            "Wireless Noise-Cancelling",
            "Headphones - Premium Black",
            "AUDIO-5521",
            "$349.99",
            "$299.99",
            # Product 2: USB-C Hub
            "USB-C Hub 7-in-1 Adapter",
            "ACC-8834",
            "$79.99",
            "$159.98",
            # Product 3: Portable SSD
            "Portable SSD 2TB",
            "STOR-2241",
            "$289.00",
            "$260.00",
            # Product 4: Wireless Mouse
            "Ergonomic Wireless Mouse",
            "ACC-9012",
            "$59.99",
            # Product 5: Screen Cleaning Kit
            "Screen Cleaning Kit",
            "CARE-1156",
            "$12.99",
            "$38.97",
            # Product 6: HDMI Cable
            "HDMI 2.1 Cable 6ft",
            "CABLE-7789",
            "$24.99",
            "$44.98",
        ]
        validate_strings(result, line_items)

        # --- Validate Totals ---
        totals = [
            "SUBTOTAL",
            "$863.91",
            "Member Discount",
            "Sales Tax (8.5%)",
            "$66.23",
            "Rewards Applied",
            "-$25.00",
            "TOTAL",
            "$821.14",
        ]
        validate_strings(result, totals)

        # --- Validate Payment Info ---
        payment_info = [
            "PAYMENT METHOD",
            "Visa Card ending in 4782",
            "Auth: 847392",
            "REF-20241123-98765",
        ]
        validate_strings(result, payment_info)

        # --- Validate Rewards Member Info ---
        rewards_info = [
            "REWARDS MEMBER",
            "Sarah Mitchell",
            "ID: TM-447821",
            "Points Earned: 821",
            "Total Points: 3,247",
        ]
        validate_strings(result, rewards_info)

        # --- Validate Return Policy & Footer ---
        footer_info = [
            "RETURN POLICY",
            "Returns within 30 days",
            "Receipt required",
            "Thank you for shopping!",
            "www.techmart.example.com",
        ]
        validate_strings(result, footer_info)

        # --- Validate Document Structure Order ---
        positions = {
            "store_header": text_content.find("TECHMART ELECTRONICS"),
            "transaction": text_content.find("TXN: TXN-98765-2024"),
            "first_item": text_content.find("Wireless Noise-Cancelling"),
            "subtotal": text_content.find("SUBTOTAL"),
            "total": text_content.find("TOTAL"),
            "payment": text_content.find("PAYMENT METHOD"),
            "rewards": text_content.find("REWARDS MEMBER"),
            "return_policy": text_content.find("RETURN POLICY"),
        }

        # All sections should be found
        for name, pos in positions.items():
            assert pos != -1, f"Section '{name}' not found in output"

        # Verify correct order
        assert (
            positions["store_header"] < positions["transaction"]
        ), "Store header should come before transaction"
        assert (
            positions["transaction"] < positions["first_item"]
        ), "Transaction should come before items"
        assert (
            positions["first_item"] < positions["subtotal"]
        ), "Items should come before subtotal"
        assert (
            positions["subtotal"] < positions["total"]
        ), "Subtotal should come before total"
        assert (
            positions["total"] < positions["payment"]
        ), "Total should come before payment"
        assert (
            positions["payment"] < positions["rewards"]
        ), "Payment should come before rewards"
        assert (
            positions["rewards"] < positions["return_policy"]
        ), "Rewards should come before return policy"