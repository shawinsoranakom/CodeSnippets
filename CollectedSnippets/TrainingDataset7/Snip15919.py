def setUpTestData(cls):
        cls.user = User.objects.create_superuser(
            username="super", password="secret", email="super@example.com"
        )
        cls.site = Site.objects.create(domain="example.org")
        cls.a1 = Article.objects.create(
            site=cls.site,
            title="Title",
            created=datetime(2008, 3, 12, 11, 54),
        )
        cls.a2 = Article.objects.create(
            site=cls.site,
            title="Title 2",
            created=datetime(2009, 3, 12, 11, 54),
        )
        cls.a3 = Article.objects.create(
            site=cls.site,
            title="Title 3",
            created=datetime(2010, 3, 12, 11, 54),
        )
        LogEntry.objects.log_actions(
            cls.user.pk,
            [cls.a1],
            CHANGE,
            change_message="Changed something",
        )