def test_callable_defaults_not_called(self):
        def raise_exception():
            raise AssertionError

        obj, created = Person.objects.get_or_create(
            first_name="John",
            last_name="Lennon",
            defaults={"birthday": lambda: raise_exception()},
        )