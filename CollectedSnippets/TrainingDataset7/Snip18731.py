def test_distinct_aggregation(self):
        class DistinctAggregate(Aggregate):
            allow_distinct = True

        aggregate = DistinctAggregate("first", "second", distinct=True)
        msg = (
            "SQLite doesn't support DISTINCT on aggregate functions accepting "
            "multiple arguments."
        )
        with self.assertRaisesMessage(NotSupportedError, msg):
            connection.ops.check_expression_support(aggregate)