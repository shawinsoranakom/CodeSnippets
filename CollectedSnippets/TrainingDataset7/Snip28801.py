def test_all_parents(self):
        self.assertEqual(CommonAncestor._meta.all_parents, ())
        self.assertEqual(FirstParent._meta.all_parents, (CommonAncestor,))
        self.assertEqual(SecondParent._meta.all_parents, (CommonAncestor,))
        self.assertEqual(
            Child._meta.all_parents,
            (FirstParent, SecondParent, CommonAncestor),
        )