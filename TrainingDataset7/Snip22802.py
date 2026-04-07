def test_changed_data(self):
        class Person(Form):
            first_name = CharField(initial="Hans")
            last_name = CharField(initial="Greatel")
            birthday = DateField(initial=datetime.date(1974, 8, 16))

        p = Person(
            data={"first_name": "Hans", "last_name": "Scrmbl", "birthday": "1974-08-16"}
        )
        self.assertTrue(p.is_valid())
        self.assertNotIn("first_name", p.changed_data)
        self.assertIn("last_name", p.changed_data)
        self.assertNotIn("birthday", p.changed_data)

        # A field raising ValidationError is always in changed_data
        class PedanticField(Field):
            def to_python(self, value):
                raise ValidationError("Whatever")

        class Person2(Person):
            pedantic = PedanticField(initial="whatever", show_hidden_initial=True)

        p = Person2(
            data={
                "first_name": "Hans",
                "last_name": "Scrmbl",
                "birthday": "1974-08-16",
                "initial-pedantic": "whatever",
            }
        )
        self.assertFalse(p.is_valid())
        self.assertIn("pedantic", p.changed_data)