def test_distinct_aggregation_multiple_args_no_distinct(self):
        # Aggregate functions accept multiple arguments when DISTINCT isn't
        # used, e.g. GROUP_CONCAT().
        class DistinctAggregate(Aggregate):
            allow_distinct = True

        aggregate = DistinctAggregate("first", "second", distinct=False)
        connection.ops.check_expression_support(aggregate)