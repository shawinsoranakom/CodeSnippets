def test_model_multiple_choice_field(self):
        f = forms.ModelMultipleChoiceField(Category.objects.all())
        self.assertCountEqual(
            list(f.choices),
            [
                (self.c1.pk, "Entertainment"),
                (self.c2.pk, "It's a test"),
                (self.c3.pk, "Third"),
            ],
        )
        with self.assertRaises(ValidationError):
            f.clean(None)
        with self.assertRaises(ValidationError):
            f.clean([])
        self.assertCountEqual(f.clean([self.c1.id]), [self.c1])
        self.assertCountEqual(f.clean([self.c2.id]), [self.c2])
        self.assertCountEqual(f.clean([str(self.c1.id)]), [self.c1])
        self.assertCountEqual(
            f.clean([str(self.c1.id), str(self.c2.id)]),
            [self.c1, self.c2],
        )
        self.assertCountEqual(
            f.clean([self.c1.id, str(self.c2.id)]),
            [self.c1, self.c2],
        )
        self.assertCountEqual(
            f.clean((self.c1.id, str(self.c2.id))),
            [self.c1, self.c2],
        )
        with self.assertRaises(ValidationError):
            f.clean(["0"])
        with self.assertRaises(ValidationError):
            f.clean("hello")
        with self.assertRaises(ValidationError):
            f.clean(["fail"])

        # Invalid types that require TypeError to be caught (#22808).
        with self.assertRaises(ValidationError):
            f.clean([["fail"]])
        with self.assertRaises(ValidationError):
            f.clean([{"foo": "bar"}])

        # Add a Category object *after* the ModelMultipleChoiceField has
        # already been instantiated. This proves clean() checks the database
        # during clean() rather than caching it at time of instantiation. Note,
        # we are using an id of 1006 here since tests that run before this may
        # create categories with primary keys up to 6. Use a number that will
        # not conflict.
        c6 = Category.objects.create(id=1006, name="Sixth", url="6th")
        self.assertCountEqual(f.clean([c6.id]), [c6])

        # Delete a Category object *after* the ModelMultipleChoiceField has
        # already been instantiated. This proves clean() checks the database
        # during clean() rather than caching it at time of instantiation.
        Category.objects.get(url="6th").delete()
        with self.assertRaises(ValidationError):
            f.clean([c6.id])