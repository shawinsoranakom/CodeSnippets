def test_ticket7872(self):
        # Another variation on the disjunctive filtering theme.

        # For the purposes of this regression test, it's important that there
        # is no Join object related to the LeafA we create.
        l1 = LeafA.objects.create(data="first")
        self.assertSequenceEqual(LeafA.objects.all(), [l1])
        self.assertSequenceEqual(
            LeafA.objects.filter(Q(data="first") | Q(join__b__data="second")),
            [l1],
        )