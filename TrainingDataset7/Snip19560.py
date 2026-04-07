def test_order_by_comments_id_count(self):
        self.assertSequenceEqual(
            User.objects.annotate(comments_count=Count("comments__id")).order_by(
                "-comments_count"
            ),
            (self.user_3, self.user_1, self.user_2),
        )