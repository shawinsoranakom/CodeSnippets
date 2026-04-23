def test_defaults_not_evaluated_unless_needed(self):
        """`defaults` aren't evaluated if the instance isn't created."""

        def raise_exception():
            raise AssertionError

        obj, created = Person.objects.get_or_create(
            first_name="John",
            defaults=lazy(raise_exception, object)(),
        )
        self.assertFalse(created)