def test_inherited_models_selects(self):
        """
        #24156 - Objects from child models where the parent's m2m field uses
        related_name='+' should be retrieved correctly.
        """
        a = InheritedArticleA.objects.create()
        b = InheritedArticleB.objects.create()
        a.publications.add(self.p1, self.p2)
        self.assertSequenceEqual(
            a.publications.all(),
            [self.p2, self.p1],
        )
        self.assertSequenceEqual(b.publications.all(), [])
        b.publications.add(self.p3)
        self.assertSequenceEqual(
            a.publications.all(),
            [self.p2, self.p1],
        )
        self.assertSequenceEqual(b.publications.all(), [self.p3])