def test_exclude_pk_in_full_none(self):
        self.assertQuerySetEqual(
            User.objects.exclude(pk__in=[(None, None)]), [self.user]
        )