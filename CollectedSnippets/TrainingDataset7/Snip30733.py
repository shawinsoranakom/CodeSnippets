def test_conflicting_aliases_during_combine(self):
        qs1 = self.annotation_1.baseuser_set.all()
        qs2 = BaseUser.objects.filter(
            Q(owner__note__in=self.annotation_1.notes.all())
            | Q(creator__note__in=self.annotation_1.notes.all())
        )
        self.assertSequenceEqual(qs1, [self.base_user_1])
        self.assertSequenceEqual(qs2, [self.base_user_2])
        self.assertCountEqual(qs2 | qs1, qs1 | qs2)
        self.assertCountEqual(qs2 | qs1, [self.base_user_1, self.base_user_2])