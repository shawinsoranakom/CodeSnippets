def test_null_fk(self):
        d = SystemDetails.objects.create(details="First details")
        s = SystemInfo.objects.create(system_name="First forum", system_details=d)
        f = Forum.objects.create(system_info=s, forum_name="First forum")
        p = Post.objects.create(forum=f, title="First Post")
        c1 = Comment.objects.create(post=p, comment_text="My first comment")
        c2 = Comment.objects.create(comment_text="My second comment")

        # Starting from comment, make sure that a .select_related(...) with a
        # specified set of fields will properly LEFT JOIN multiple levels of
        # NULLs (and the things that come after the NULLs, or else data that
        # should exist won't). Regression test for #7369.
        c = Comment.objects.select_related().get(id=c1.id)
        self.assertEqual(c.post, p)
        self.assertIsNone(Comment.objects.select_related().get(id=c2.id).post)

        self.assertQuerySetEqual(
            Comment.objects.select_related("post__forum__system_info").all(),
            [
                (c1.id, "My first comment", "<Post: First Post>"),
                (c2.id, "My second comment", "None"),
            ],
            transform=lambda c: (c.id, c.comment_text, repr(c.post)),
        )

        # Regression test for #7530, #7716.
        self.assertIsNone(
            Comment.objects.select_related("post").filter(post__isnull=True)[0].post
        )

        self.assertQuerySetEqual(
            Comment.objects.select_related("post__forum__system_info__system_details"),
            [
                (c1.id, "My first comment", "<Post: First Post>"),
                (c2.id, "My second comment", "None"),
            ],
            transform=lambda c: (c.id, c.comment_text, repr(c.post)),
        )