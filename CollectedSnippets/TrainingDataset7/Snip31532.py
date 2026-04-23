def test_for_update_sql_multilevel_model_inheritance_ptr_generated_of(self):
        with transaction.atomic(), CaptureQueriesContext(connection) as ctx:
            list(
                EUCountry.objects.select_for_update(
                    of=("country_ptr", "country_ptr__entity_ptr"),
                )
            )
        if connection.features.select_for_update_of_column:
            expected = [
                'select_for_update_country"."entity_ptr_id',
                'select_for_update_entity"."id',
            ]
        else:
            expected = ["select_for_update_country", "select_for_update_entity"]
        expected = [connection.ops.quote_name(value) for value in expected]
        self.assertTrue(self.has_for_update_sql(ctx.captured_queries, of=expected))