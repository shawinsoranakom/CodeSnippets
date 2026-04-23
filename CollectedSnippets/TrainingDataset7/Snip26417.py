def test_remove_from_wrong_set(self):
        self.assertSequenceEqual(self.r2.article_set.all(), [self.a4])
        # Try to remove a4 from a set it does not belong to
        with self.assertRaises(Reporter.DoesNotExist):
            self.r.article_set.remove(self.a4)
        self.assertSequenceEqual(self.r2.article_set.all(), [self.a4])