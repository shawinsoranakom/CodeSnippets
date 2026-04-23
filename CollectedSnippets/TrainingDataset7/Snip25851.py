def test_custom_field_none_rhs(self):
        """
        __exact=value is transformed to __isnull=True if Field.get_prep_value()
        converts value to None.
        """
        season = Season.objects.create(year=2012, nulled_text_field=None)
        self.assertTrue(
            Season.objects.filter(pk=season.pk, nulled_text_field__isnull=True)
        )
        self.assertTrue(Season.objects.filter(pk=season.pk, nulled_text_field=""))