def test_values_with_extra(self):
        """
        Regression test for #10256... If there is a values() clause, Extra
        columns are only returned if they are explicitly mentioned.
        """
        obj = TestObject(first="first", second="second", third="third")
        obj.save()

        self.assertEqual(
            list(
                TestObject.objects.extra(
                    select={"foo": "first", "bar": "second", "whiz": "third"}
                ).values()
            ),
            [
                {
                    "bar": "second",
                    "third": "third",
                    "second": "second",
                    "whiz": "third",
                    "foo": "first",
                    "id": obj.pk,
                    "first": "first",
                }
            ],
        )

        # Extra clauses after an empty values clause are still included
        self.assertEqual(
            list(
                TestObject.objects.values().extra(
                    select={"foo": "first", "bar": "second", "whiz": "third"}
                )
            ),
            [
                {
                    "bar": "second",
                    "third": "third",
                    "second": "second",
                    "whiz": "third",
                    "foo": "first",
                    "id": obj.pk,
                    "first": "first",
                }
            ],
        )

        # Extra columns are ignored if not mentioned in the values() clause
        self.assertEqual(
            list(
                TestObject.objects.extra(
                    select={"foo": "first", "bar": "second", "whiz": "third"}
                ).values("first", "second")
            ),
            [{"second": "second", "first": "first"}],
        )

        # Extra columns after a non-empty values() clause are ignored
        self.assertEqual(
            list(
                TestObject.objects.values("first", "second").extra(
                    select={"foo": "first", "bar": "second", "whiz": "third"}
                )
            ),
            [{"second": "second", "first": "first"}],
        )

        # Extra columns can be partially returned
        self.assertEqual(
            list(
                TestObject.objects.extra(
                    select={"foo": "first", "bar": "second", "whiz": "third"}
                ).values("first", "second", "foo")
            ),
            [{"second": "second", "foo": "first", "first": "first"}],
        )

        # Also works if only extra columns are included
        self.assertEqual(
            list(
                TestObject.objects.extra(
                    select={"foo": "first", "bar": "second", "whiz": "third"}
                ).values("foo", "whiz")
            ),
            [{"foo": "first", "whiz": "third"}],
        )

        # Values list works the same way
        # All columns are returned for an empty values_list()
        self.assertEqual(
            list(
                TestObject.objects.extra(
                    select={"foo": "first", "bar": "second", "whiz": "third"}
                ).values_list()
            ),
            [("first", "second", "third", obj.pk, "first", "second", "third")],
        )

        # Extra columns after an empty values_list() are still included
        self.assertEqual(
            list(
                TestObject.objects.values_list().extra(
                    select={"foo": "first", "bar": "second", "whiz": "third"}
                )
            ),
            [("first", "second", "third", obj.pk, "first", "second", "third")],
        )

        # Extra columns ignored completely if not mentioned in values_list()
        self.assertEqual(
            list(
                TestObject.objects.extra(
                    select={"foo": "first", "bar": "second", "whiz": "third"}
                ).values_list("first", "second")
            ),
            [("first", "second")],
        )

        # Extra columns after a non-empty values_list() clause are ignored
        # completely
        self.assertEqual(
            list(
                TestObject.objects.values_list("first", "second").extra(
                    select={"foo": "first", "bar": "second", "whiz": "third"}
                )
            ),
            [("first", "second")],
        )

        self.assertEqual(
            list(
                TestObject.objects.extra(
                    select={"foo": "first", "bar": "second", "whiz": "third"}
                ).values_list("second", flat=True)
            ),
            ["second"],
        )

        # Only the extra columns specified in the values_list() are returned
        self.assertEqual(
            list(
                TestObject.objects.extra(
                    select={"foo": "first", "bar": "second", "whiz": "third"}
                ).values_list("first", "second", "whiz")
            ),
            [("first", "second", "third")],
        )

        # ...also works if only extra columns are included
        self.assertEqual(
            list(
                TestObject.objects.extra(
                    select={"foo": "first", "bar": "second", "whiz": "third"}
                ).values_list("foo", "whiz")
            ),
            [("first", "third")],
        )

        self.assertEqual(
            list(
                TestObject.objects.extra(
                    select={"foo": "first", "bar": "second", "whiz": "third"}
                ).values_list("whiz", flat=True)
            ),
            ["third"],
        )

        # ... and values are returned in the order they are specified
        self.assertEqual(
            list(
                TestObject.objects.extra(
                    select={"foo": "first", "bar": "second", "whiz": "third"}
                ).values_list("whiz", "foo")
            ),
            [("third", "first")],
        )

        self.assertEqual(
            list(
                TestObject.objects.extra(
                    select={"foo": "first", "bar": "second", "whiz": "third"}
                ).values_list("first", "id")
            ),
            [("first", obj.pk)],
        )

        self.assertEqual(
            list(
                TestObject.objects.extra(
                    select={"foo": "first", "bar": "second", "whiz": "third"}
                ).values_list("whiz", "first", "bar", "id")
            ),
            [("third", "first", "second", obj.pk)],
        )