def test_get_db_prep_value(self):
        """
        DecimalField.get_db_prep_value() must call
        DatabaseOperations.adapt_decimalfield_value().
        """
        f = models.DecimalField(max_digits=5, decimal_places=1)
        # None of the built-in database backends implement
        # adapt_decimalfield_value(), so this must be confirmed with mocking.
        with mock.patch.object(
            connection.ops.__class__, "adapt_decimalfield_value"
        ) as adapt_decimalfield_value:
            f.get_db_prep_value("2.4", connection)
        adapt_decimalfield_value.assert_called_with(Decimal("2.4"), 5, 1)