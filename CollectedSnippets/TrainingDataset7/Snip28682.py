def test_model_with_distinct_accessors(self):
        # The Post model has distinct accessors for the Comment and Link
        # models.
        post = Post.objects.create(title="Lorem Ipsum")
        post.attached_comment_set.create(content="Save $ on V1agr@", is_spam=True)
        post.attached_link_set.create(
            content="The web framework for perfections with deadlines.",
            url="http://www.djangoproject.com/",
        )

        # The Post model doesn't have an attribute called
        # 'attached_%(class)s_set'.
        msg = "'Post' object has no attribute 'attached_%(class)s_set'"
        with self.assertRaisesMessage(AttributeError, msg):
            getattr(post, "attached_%(class)s_set")