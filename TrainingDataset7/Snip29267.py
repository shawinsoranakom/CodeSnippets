def test_filter_one_to_one_relations(self):
        """
        Regression test for #9968

        filtering reverse one-to-one relations with primary_key=True was
        misbehaving. We test both (primary_key=True & False) cases here to
        prevent any reappearance of the problem.
        """
        target = Target.objects.create()
        self.assertSequenceEqual(Target.objects.filter(pointer=None), [target])
        self.assertSequenceEqual(Target.objects.exclude(pointer=None), [])
        self.assertSequenceEqual(Target.objects.filter(second_pointer=None), [target])
        self.assertSequenceEqual(Target.objects.exclude(second_pointer=None), [])