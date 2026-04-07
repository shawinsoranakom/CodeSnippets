def test_update_parent_filtering(self):
        """
        Updating a field of a model subclass doesn't issue an UPDATE
        query constrained by an inner query (#10399).
        """
        supplier = Supplier.objects.create(
            name="Central market",
            address="610 some street",
        )
        # Capture the expected query in a database agnostic way
        with CaptureQueriesContext(connection) as captured_queries:
            Place.objects.filter(pk=supplier.pk).update(name=supplier.name)
        expected_sql = captured_queries[0]["sql"]
        # Capture the queries executed when a subclassed model instance is
        # saved.
        with CaptureQueriesContext(connection) as captured_queries:
            supplier.save(update_fields=("name",))
        for query in captured_queries:
            sql = query["sql"]
            if "UPDATE" in sql:
                self.assertEqual(expected_sql, sql)