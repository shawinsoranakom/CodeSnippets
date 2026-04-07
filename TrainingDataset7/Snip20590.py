def test_gt_two_expressions(self):
        with self.assertRaisesMessage(
            ValueError, "Concat must take at least two expressions"
        ):
            Author.objects.annotate(joined=Concat("alias"))