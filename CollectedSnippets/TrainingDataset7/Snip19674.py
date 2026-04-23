def test_bulk_update_comments(self):
        comment_1 = Comment.objects.get(pk=self.comment_1.pk)
        comment_2 = Comment.objects.get(pk=self.comment_2.pk)
        comment_3 = Comment.objects.get(pk=self.comment_3.pk)
        comment_1.text = "foo"
        comment_2.text = "bar"
        comment_3.text = "baz"

        result = Comment.objects.bulk_update(
            [comment_1, comment_2, comment_3], ["text"]
        )

        self.assertEqual(result, 3)
        comment_1 = Comment.objects.get(pk=self.comment_1.pk)
        comment_2 = Comment.objects.get(pk=self.comment_2.pk)
        comment_3 = Comment.objects.get(pk=self.comment_3.pk)
        self.assertEqual(comment_1.text, "foo")
        self.assertEqual(comment_2.text, "bar")
        self.assertEqual(comment_3.text, "baz")