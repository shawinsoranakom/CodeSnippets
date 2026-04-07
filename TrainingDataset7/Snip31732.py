def natural_key_opt_out_test(self, format):
    """
    When a subclass of AbstractBaseUser opts out of natural key serialization
    by returning an empty tuple, both FK and M2M relations serialize as
    integer PKs and can be deserialized without error.
    """
    user1 = SubclassNaturalKeyOptOutUser.objects.create(email="user1@example.com")
    user2 = SubclassNaturalKeyOptOutUser.objects.create(email="user2@example.com")

    post = PostToOptOutSubclassUser.objects.create(
        author=user1, title="Post 2 (Subclass Opt-out)"
    )
    post.subscribers.add(user1, user2)

    user_data = serializers.serialize(format, [user1], use_natural_primary_keys=True)
    post_data = serializers.serialize(format, [post], use_natural_foreign_keys=True)

    list(serializers.deserialize(format, user_data))
    deserialized_posts = list(serializers.deserialize(format, post_data))

    post_obj = deserialized_posts[0].object
    self.assertEqual(user1.email, post_obj.author.email)
    self.assertEqual(
        sorted([user1.email, user2.email]),
        sorted(post_obj.subscribers.values_list("email", flat=True)),
    )