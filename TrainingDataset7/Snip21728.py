def test_regression_17877(self):
        """
        Extra WHERE clauses get correctly ANDed, even when they
        contain OR operations.
        """
        # Test Case 1: should appear in queryset.
        t1 = TestObject.objects.create(first="a", second="a", third="a")
        # Test Case 2: should appear in queryset.
        t2 = TestObject.objects.create(first="b", second="a", third="a")
        # Test Case 3: should not appear in queryset, bug case.
        t = TestObject(first="a", second="a", third="b")
        t.save()
        # Test Case 4: should not appear in queryset.
        t = TestObject(first="b", second="a", third="b")
        t.save()
        # Test Case 5: should not appear in queryset.
        t = TestObject(first="b", second="b", third="a")
        t.save()
        # Test Case 6: should not appear in queryset, bug case.
        t = TestObject(first="a", second="b", third="b")
        t.save()

        self.assertCountEqual(
            TestObject.objects.extra(
                where=["first = 'a' OR second = 'a'", "third = 'a'"],
            ),
            [t1, t2],
        )