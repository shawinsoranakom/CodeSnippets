def test_setter(self):
        # The "full_name" property hasn't provided a "set" method.
        with self.assertRaises(AttributeError):
            setattr(self.a, "full_name", "Paul McCartney")

        # And cannot be used to initialize the class.
        with self.assertRaises(AttributeError):
            Person(full_name="Paul McCartney")

        # But "full_name_2" has, and it can be used to initialize the class.
        a2 = Person(full_name_2="Paul McCartney")
        a2.save()
        self.assertEqual(a2.first_name, "Paul")