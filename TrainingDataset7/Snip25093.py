def test_localized_input(self):
        """
        Tests if form input is correctly localized
        """
        self.maxDiff = 1200
        with translation.override("de-at", deactivate=True):
            form6 = CompanyForm(
                {
                    "name": "acme",
                    "date_added": datetime.datetime(2009, 12, 31, 6, 0, 0),
                    "cents_paid": decimal.Decimal("59.47"),
                    "products_delivered": 12000,
                }
            )
            self.assertTrue(form6.is_valid())
            self.assertHTMLEqual(
                form6.as_ul(),
                '<li><label for="id_name">Name:</label>'
                '<input id="id_name" type="text" name="name" value="acme" '
                '   maxlength="50" required></li>'
                '<li><label for="id_date_added">Date added:</label>'
                '<input type="text" name="date_added" value="31.12.2009 06:00:00" '
                '   id="id_date_added" required></li>'
                '<li><label for="id_cents_paid">Cents paid:</label>'
                '<input type="text" name="cents_paid" value="59,47" id="id_cents_paid" '
                "   required></li>"
                '<li><label for="id_products_delivered">Products delivered:</label>'
                '<input type="text" name="products_delivered" value="12000" '
                '   id="id_products_delivered" required>'
                "</li>",
            )
            self.assertEqual(
                localize_input(datetime.datetime(2009, 12, 31, 6, 0, 0)),
                "31.12.2009 06:00:00",
            )
            self.assertEqual(
                datetime.datetime(2009, 12, 31, 6, 0, 0),
                form6.cleaned_data["date_added"],
            )
            with self.settings(USE_THOUSAND_SEPARATOR=True):
                # Checking for the localized "products_delivered" field
                self.assertInHTML(
                    '<input type="text" name="products_delivered" '
                    'value="12.000" id="id_products_delivered" required>',
                    form6.as_ul(),
                )