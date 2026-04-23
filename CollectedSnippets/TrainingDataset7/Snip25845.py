def test_exact_none_transform(self):
        """Transforms are used for __exact=None."""
        Season.objects.create(year=1, nulled_text_field="not null")
        self.assertFalse(Season.objects.filter(nulled_text_field__isnull=True))
        self.assertTrue(Season.objects.filter(nulled_text_field__nulled__isnull=True))
        self.assertTrue(Season.objects.filter(nulled_text_field__nulled__exact=None))
        self.assertTrue(Season.objects.filter(nulled_text_field__nulled=None))