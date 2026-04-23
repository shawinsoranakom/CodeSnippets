def test_regression_10847(self):
        """
        Regression for #10847: the list of extra columns can always be
        accurately evaluated. Using an inner query ensures that as_sql() is
        producing correct output without requiring full evaluation and
        execution of the inner query.
        """
        obj = TestObject(first="first", second="second", third="third")
        obj.save()

        self.assertEqual(
            list(TestObject.objects.extra(select={"extra": 1}).values("pk")),
            [{"pk": obj.pk}],
        )

        self.assertSequenceEqual(
            TestObject.objects.filter(
                pk__in=TestObject.objects.extra(select={"extra": 1}).values("pk")
            ),
            [obj],
        )

        self.assertEqual(
            list(TestObject.objects.values("pk").extra(select={"extra": 1})),
            [{"pk": obj.pk}],
        )

        self.assertSequenceEqual(
            TestObject.objects.filter(
                pk__in=TestObject.objects.values("pk").extra(select={"extra": 1})
            ),
            [obj],
        )

        self.assertSequenceEqual(
            TestObject.objects.filter(pk=obj.pk)
            | TestObject.objects.extra(where=["id > %s"], params=[obj.pk]),
            [obj],
        )