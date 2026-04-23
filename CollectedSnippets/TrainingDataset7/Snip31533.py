def test_for_update_sql_model_proxy_generated_of(self):
        with transaction.atomic(), CaptureQueriesContext(connection) as ctx:
            list(
                CityCountryProxy.objects.select_related("country").select_for_update(
                    of=("country",),
                )
            )
        if connection.features.select_for_update_of_column:
            expected = ['select_for_update_country"."entity_ptr_id']
        else:
            expected = ["select_for_update_country"]
        expected = [connection.ops.quote_name(value) for value in expected]
        self.assertTrue(self.has_for_update_sql(ctx.captured_queries, of=expected))