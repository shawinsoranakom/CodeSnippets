def test_choices_radio_blank(self):
        choices = [
            (self.c1.pk, "Entertainment"),
            (self.c2.pk, "A test"),
            (self.c3.pk, "Third"),
        ]
        categories = Category.objects.order_by("pk")
        for widget in [forms.RadioSelect, forms.RadioSelect()]:
            for blank in [True, False]:
                with self.subTest(widget=widget, blank=blank):
                    f = forms.ModelChoiceField(
                        categories,
                        widget=widget,
                        blank=blank,
                    )
                    self.assertEqual(
                        list(f.choices),
                        [("", "---------")] + choices if blank else choices,
                    )