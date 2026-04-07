def test_choices_freshness(self):
        f = forms.ModelChoiceField(Category.objects.order_by("pk"))
        self.assertEqual(len(f.choices), 4)
        self.assertEqual(
            list(f.choices),
            [
                ("", "---------"),
                (self.c1.pk, "Entertainment"),
                (self.c2.pk, "A test"),
                (self.c3.pk, "Third"),
            ],
        )
        c4 = Category.objects.create(name="Fourth", slug="4th", url="4th")
        self.assertEqual(len(f.choices), 5)
        self.assertEqual(
            list(f.choices),
            [
                ("", "---------"),
                (self.c1.pk, "Entertainment"),
                (self.c2.pk, "A test"),
                (self.c3.pk, "Third"),
                (c4.pk, "Fourth"),
            ],
        )