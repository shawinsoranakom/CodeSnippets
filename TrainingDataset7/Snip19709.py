def test_iterator(self):
        """
        Test the .iterator() method of composite_pk models.
        """
        result = list(Comment.objects.iterator())
        self.assertEqual(result, [self.comment])