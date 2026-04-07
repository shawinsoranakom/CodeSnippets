def test_for_update_sql_generated_of(self):
        """
        The backend's FOR UPDATE OF variant appears in the generated SQL when
        select_for_update() is invoked.
        """
        with transaction.atomic(), CaptureQueriesContext(connection) as ctx:
            list(
                Person.objects.select_related(
                    "born__country",
                )
                .select_for_update(
                    of=("born__country",),
                )
                .select_for_update(of=("self", "born__country"))
            )
        features = connections["default"].features
        if features.select_for_update_of_column:
            expected = [
                'select_for_update_person"."id',
                'select_for_update_country"."entity_ptr_id',
            ]
        else:
            expected = ["select_for_update_person", "select_for_update_country"]
        expected = [connection.ops.quote_name(value) for value in expected]
        self.assertTrue(self.has_for_update_sql(ctx.captured_queries, of=expected))