def test_model_multiple_choice_required_false(self):
        f = forms.ModelMultipleChoiceField(Category.objects.all(), required=False)
        self.assertIsInstance(f.clean([]), EmptyQuerySet)
        self.assertIsInstance(f.clean(()), EmptyQuerySet)
        with self.assertRaises(ValidationError):
            f.clean(["0"])
        with self.assertRaises(ValidationError):
            f.clean([str(self.c3.id), "0"])
        with self.assertRaises(ValidationError):
            f.clean([str(self.c1.id), "0"])

        # queryset can be changed after the field is created.
        f.queryset = Category.objects.exclude(name="Third")
        self.assertCountEqual(
            list(f.choices),
            [(self.c1.pk, "Entertainment"), (self.c2.pk, "It's a test")],
        )
        self.assertSequenceEqual(f.clean([self.c2.id]), [self.c2])
        with self.assertRaises(ValidationError):
            f.clean([self.c3.id])
        with self.assertRaises(ValidationError):
            f.clean([str(self.c2.id), str(self.c3.id)])

        f.queryset = Category.objects.all()
        f.label_from_instance = lambda obj: "multicategory " + str(obj)
        self.assertCountEqual(
            list(f.choices),
            [
                (self.c1.pk, "multicategory Entertainment"),
                (self.c2.pk, "multicategory It's a test"),
                (self.c3.pk, "multicategory Third"),
            ],
        )