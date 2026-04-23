def test_xor_subquery(self):
        self.assertSequenceEqual(
            Tag.objects.filter(
                Exists(Tag.objects.filter(id=OuterRef("id"), name="t3"))
                ^ Exists(Tag.objects.filter(id=OuterRef("id"), parent=self.t1))
            ),
            [self.t2],
        )