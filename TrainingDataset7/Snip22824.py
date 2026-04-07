def test_class_prefix(self):
        # Prefix can be also specified at the class level.
        class Person(Form):
            first_name = CharField()
            prefix = "foo"

        p = Person()
        self.assertEqual(p.prefix, "foo")

        p = Person(prefix="bar")
        self.assertEqual(p.prefix, "bar")