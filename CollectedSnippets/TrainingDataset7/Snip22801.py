def test_get_initial_for_field(self):
        now = datetime.datetime(2006, 10, 25, 14, 30, 45, 123456)

        class PersonForm(Form):
            first_name = CharField(initial="John")
            last_name = CharField(initial="Doe")
            age = IntegerField()
            occupation = CharField(initial=lambda: "Unknown")
            dt_fixed = DateTimeField(initial=now)
            dt_callable = DateTimeField(initial=lambda: now)

        form = PersonForm(initial={"first_name": "Jane"})
        cases = [
            ("age", None),
            ("last_name", "Doe"),
            # Form.initial overrides Field.initial.
            ("first_name", "Jane"),
            # Callables are evaluated.
            ("occupation", "Unknown"),
            # Microseconds are removed from datetimes.
            ("dt_fixed", datetime.datetime(2006, 10, 25, 14, 30, 45)),
            ("dt_callable", datetime.datetime(2006, 10, 25, 14, 30, 45)),
        ]
        for field_name, expected in cases:
            with self.subTest(field_name=field_name):
                field = form.fields[field_name]
                actual = form.get_initial_for_field(field, field_name)
                self.assertEqual(actual, expected)