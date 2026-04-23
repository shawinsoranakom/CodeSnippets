def test_model_with_distinct_related_query_name(self):
        self.assertSequenceEqual(
            Post.objects.filter(attached_model_inheritance_comments__is_spam=True), []
        )

        # The Post model doesn't have a related query accessor based on
        # related_name (attached_comment_set).
        msg = "Cannot resolve keyword 'attached_comment_set' into field."
        with self.assertRaisesMessage(FieldError, msg):
            Post.objects.filter(attached_comment_set__is_spam=True)