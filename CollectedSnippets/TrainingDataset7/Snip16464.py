def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(
            username="super", password="secret", email="super@example.com"
        )
        cls.s1 = Section.objects.create(name="Test section")
        cls.a1 = Article.objects.create(
            content="<p>Middle content</p>",
            date=datetime.datetime(2008, 3, 18, 11, 54, 58),
            section=cls.s1,
        )
        cls.a2 = Article.objects.create(
            content="<p>Oldest content</p>",
            date=datetime.datetime(2000, 3, 18, 11, 54, 58),
            section=cls.s1,
        )
        cls.a3 = Article.objects.create(
            content="<p>Newest content</p>",
            date=datetime.datetime(2009, 3, 18, 11, 54, 58),
            section=cls.s1,
        )
        cls.p1 = PrePopulatedPost.objects.create(
            title="A Long Title", published=True, slug="a-long-title"
        )
        cls.pk = (
            "abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ 1234567890 "
            r"""-_.!~*'() ;/?:@&=+$, <>#%" {}|\^[]`"""
        )
        cls.m1 = ModelWithStringPrimaryKey.objects.create(string_pk=cls.pk)
        user_pk = cls.superuser.pk
        LogEntry.objects.log_actions(
            user_pk,
            [cls.m1],
            2,
            change_message="Changed something",
        )
        LogEntry.objects.log_actions(
            user_pk,
            [cls.m1],
            1,
            change_message="Added something",
        )
        LogEntry.objects.log_actions(
            user_pk,
            [cls.m1],
            3,
            change_message="Deleted something",
        )