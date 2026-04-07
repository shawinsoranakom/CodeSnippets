def test_update_fields_incorrect_params(self):
        s = Person.objects.create(name="Sara", gender="F")

        with self.assertRaisesMessage(ValueError, self.msg % "first_name"):
            s.save(update_fields=["first_name"])

        # "name" is treated as an iterable so the output is something like
        # "n, a, m, e" but the order isn't deterministic.
        with self.assertRaisesMessage(ValueError, self.msg % ""):
            s.save(update_fields="name")