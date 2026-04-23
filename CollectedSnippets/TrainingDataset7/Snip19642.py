def test_exclude_pk_in_partial_none(self):
        self.assertQuerySetEqual(
            User.objects.exclude(pk__in=[(self.user.pk[0], None)]), [self.user]
        )