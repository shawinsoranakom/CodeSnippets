def test_queryset_manager(self):
        f = forms.ModelChoiceField(Category.objects)
        self.assertEqual(len(f.choices), 4)
        self.assertCountEqual(
            list(f.choices),
            [
                ("", "---------"),
                (self.c1.pk, "Entertainment"),
                (self.c2.pk, "A test"),
                (self.c3.pk, "Third"),
            ],
        )