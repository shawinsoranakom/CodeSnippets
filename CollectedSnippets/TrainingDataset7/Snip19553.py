def test_users_annotated_with_aliased_comments_id_count(self):
        user_1, user_2, user_3 = User.objects.annotate(
            comments_count=Count("comments__id")
        ).order_by("pk")

        self.assertEqual(user_1, self.user_1)
        self.assertEqual(user_1.comments_count, 2)
        self.assertEqual(user_2, self.user_2)
        self.assertEqual(user_2.comments_count, 1)
        self.assertEqual(user_3, self.user_3)
        self.assertEqual(user_3.comments_count, 3)