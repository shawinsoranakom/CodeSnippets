def test_get_prep_value(self):
        class JSONFieldGetPrepValue(models.JSONField):
            def get_prep_value(self, value):
                if value is True:
                    return {"value": True}
                return value

        def noop_adapt_json_value(value, encoder):
            return value

        field = JSONFieldGetPrepValue()
        with mock.patch.object(
            connection.ops, "adapt_json_value", noop_adapt_json_value
        ):
            self.assertEqual(
                field.get_db_prep_value(True, connection, prepared=False),
                {"value": True},
            )
            self.assertIs(
                field.get_db_prep_value(True, connection, prepared=True), True
            )
            self.assertEqual(field.get_db_prep_value(1, connection, prepared=False), 1)