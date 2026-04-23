def test_filter_pk_in_partial_none(self):
        self.assertQuerySetEqual(
            User.objects.filter(pk__in=[(self.user.pk[0], None)]), []
        )