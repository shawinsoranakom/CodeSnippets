def test_prefetch_related_queryset(self):
        """
        ModelChoiceField should respect a prefetch_related() on its queryset.
        """
        blue = Color.objects.create(name="blue")
        red = Color.objects.create(name="red")
        multicolor_item = ColorfulItem.objects.create()
        multicolor_item.colors.add(blue, red)
        red_item = ColorfulItem.objects.create()
        red_item.colors.add(red)

        class ColorModelChoiceField(forms.ModelChoiceField):
            def label_from_instance(self, obj):
                return ", ".join(c.name for c in obj.colors.all())

        field = ColorModelChoiceField(ColorfulItem.objects.prefetch_related("colors"))
        # CPython < 3.14 calls ModelChoiceField.__len__() when coercing to
        # tuple. PyPy and Python 3.14+ don't call __len__() and so .count()
        # isn't called on the QuerySet. The following would trigger an extra
        # query if prefetch were ignored.
        with self.assertNumQueries(2 if PYPY or PY314 else 3):
            self.assertEqual(
                tuple(field.choices),
                (
                    ("", "---------"),
                    (multicolor_item.pk, "blue, red"),
                    (red_item.pk, "red"),
                ),
            )