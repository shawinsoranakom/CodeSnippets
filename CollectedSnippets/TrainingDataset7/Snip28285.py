def test_choices(self):
        f = forms.ModelChoiceField(
            Category.objects.filter(pk=self.c1.id), required=False
        )
        self.assertIsNone(f.clean(""))
        self.assertEqual(f.clean(str(self.c1.id)).name, "Entertainment")
        with self.assertRaises(ValidationError):
            f.clean("100")

        # len() can be called on choices.
        self.assertEqual(len(f.choices), 2)

        # queryset can be changed after the field is created.
        f.queryset = Category.objects.exclude(name="Third").order_by("pk")
        self.assertEqual(
            list(f.choices),
            [
                ("", "---------"),
                (self.c1.pk, "Entertainment"),
                (self.c2.pk, "A test"),
            ],
        )
        self.assertEqual(f.clean(self.c2.id).name, "A test")
        with self.assertRaises(ValidationError):
            f.clean(self.c3.id)

        # Choices can be iterated repeatedly.
        gen_one = list(f.choices)
        gen_two = f.choices
        self.assertEqual(gen_one[2], (self.c2.pk, "A test"))
        self.assertEqual(
            list(gen_two),
            [
                ("", "---------"),
                (self.c1.pk, "Entertainment"),
                (self.c2.pk, "A test"),
            ],
        )

        # Overriding label_from_instance() to print custom labels.
        f.queryset = Category.objects.order_by("pk")
        f.label_from_instance = lambda obj: "category " + str(obj)
        self.assertEqual(
            list(f.choices),
            [
                ("", "---------"),
                (self.c1.pk, "category Entertainment"),
                (self.c2.pk, "category A test"),
                (self.c3.pk, "category Third"),
            ],
        )