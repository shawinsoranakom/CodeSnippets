def test_for_update_sql_related_model_inheritance_generated_of(self):
        with transaction.atomic(), CaptureQueriesContext(connection) as ctx:
            list(
                EUCity.objects.select_related("country").select_for_update(
                    of=("self", "country"),
                )
            )
        if connection.features.select_for_update_of_column:
            expected = [
                'select_for_update_eucity"."id',
                'select_for_update_eucountry"."country_ptr_id',
            ]
        else:
            expected = ["select_for_update_eucity", "select_for_update_eucountry"]
        expected = [connection.ops.quote_name(value) for value in expected]
        self.assertTrue(self.has_for_update_sql(ctx.captured_queries, of=expected))