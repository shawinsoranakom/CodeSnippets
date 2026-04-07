def test_inherited_nullable_exclude(self):
        obj = SelfRefChild.objects.create(child_data=37, parent_data=42)
        self.assertQuerySetEqual(
            SelfRefParent.objects.exclude(self_data=72), [obj.pk], attrgetter("pk")
        )
        self.assertQuerySetEqual(
            SelfRefChild.objects.exclude(self_data=72), [obj.pk], attrgetter("pk")
        )