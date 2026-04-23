def test_filter_pk_in_full_none(self):
        self.assertQuerySetEqual(User.objects.filter(pk__in=[(None, None)]), [])