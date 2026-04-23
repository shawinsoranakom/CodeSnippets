def test_in_bulk(self):
        """
        Test the .in_bulk() method of composite_pk models.
        """
        result = Comment.objects.in_bulk()
        self.assertEqual(result, {self.comment.pk: self.comment})

        result = Comment.objects.in_bulk([self.comment.pk])
        self.assertEqual(result, {self.comment.pk: self.comment})