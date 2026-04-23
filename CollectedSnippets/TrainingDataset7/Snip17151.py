def test_allow_distinct(self):
        class MyAggregate(Aggregate):
            pass

        with self.assertRaisesMessage(TypeError, "MyAggregate does not allow distinct"):
            MyAggregate("foo", distinct=True)

        class DistinctAggregate(Aggregate):
            allow_distinct = True

        DistinctAggregate("foo", distinct=True)