def test_nonempty_update(self):
        """
        Update changes the right number of rows for a nonempty queryset
        """
        num_updated = self.a1.b_set.update(y=100)
        self.assertEqual(num_updated, 20)
        cnt = B.objects.filter(y=100).count()
        self.assertEqual(cnt, 20)