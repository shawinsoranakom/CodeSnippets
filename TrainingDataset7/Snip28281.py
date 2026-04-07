def test_basics(self):
        f = forms.ModelChoiceField(Category.objects.all())
        self.assertEqual(
            list(f.choices),
            [
                ("", "---------"),
                (self.c1.pk, "Entertainment"),
                (self.c2.pk, "A test"),
                (self.c3.pk, "Third"),
            ],
        )
        with self.assertRaises(ValidationError):
            f.clean("")
        with self.assertRaises(ValidationError):
            f.clean(None)
        with self.assertRaises(ValidationError):
            f.clean(0)

        # Invalid types that require TypeError to be caught.
        with self.assertRaises(ValidationError):
            f.clean([["fail"]])
        with self.assertRaises(ValidationError):
            f.clean([{"foo": "bar"}])

        self.assertEqual(f.clean(self.c2.id).name, "A test")
        self.assertEqual(f.clean(self.c3.id).name, "Third")

        # Add a Category object *after* the ModelChoiceField has already been
        # instantiated. This proves clean() checks the database during clean()
        # rather than caching it at  instantiation time.
        c4 = Category.objects.create(name="Fourth", url="4th")
        self.assertEqual(f.clean(c4.id).name, "Fourth")

        # Delete a Category object *after* the ModelChoiceField has already
        # been instantiated. This proves clean() checks the database during
        # clean() rather than caching it at instantiation time.
        Category.objects.get(url="4th").delete()
        msg = (
            "['Select a valid choice. That choice is not one of the available "
            "choices.']"
        )
        with self.assertRaisesMessage(ValidationError, msg):
            f.clean(c4.id)