def test_union_applies_default_ordering_afterward(self):
        c = Tag.objects.create(name="C")
        Tag.objects.create(name="B")
        a = Tag.objects.create(name="A")
        qs1 = Tag.objects.filter(name__in=["A", "B"])[:1]
        qs2 = Tag.objects.filter(name__in=["C"])[:1]
        self.assertSequenceEqual(qs1.union(qs2), [a, c])