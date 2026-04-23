def test_decimal_expression(self):
        n = Number.objects.create(integer=1, decimal_value=Decimal("0.5"))
        n.decimal_value = F("decimal_value") - Decimal("0.4")
        n.save()
        expected_num_queries = (
            0 if connection.features.can_return_rows_from_update else 1
        )
        with self.assertNumQueries(expected_num_queries):
            self.assertEqual(n.decimal_value, Decimal("0.1"))