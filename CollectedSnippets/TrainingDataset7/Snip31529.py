def test_for_update_sql_model_inheritance_ptr_generated_of(self):
        with transaction.atomic(), CaptureQueriesContext(connection) as ctx:
            list(
                EUCountry.objects.select_for_update(
                    of=(
                        "self",
                        "country_ptr",
                    )
                )
            )
        if connection.features.select_for_update_of_column:
            expected = [
                'select_for_update_eucountry"."country_ptr_id',
                'select_for_update_country"."entity_ptr_id',
            ]
        else:
            expected = ["select_for_update_eucountry", "select_for_update_country"]
        expected = [connection.ops.quote_name(value) for value in expected]
        self.assertTrue(self.has_for_update_sql(ctx.captured_queries, of=expected))