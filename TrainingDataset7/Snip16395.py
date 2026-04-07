def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(
            username="super", password="secret", email="super@example.com"
        )
        cls.viewuser = User.objects.create_user(
            username="viewuser", password="secret", is_staff=True
        )
        cls.adduser = User.objects.create_user(
            username="adduser", password="secret", is_staff=True
        )
        cls.changeuser = User.objects.create_user(
            username="changeuser", password="secret", is_staff=True
        )
        cls.deleteuser = User.objects.create_user(
            username="deleteuser", password="secret", is_staff=True
        )
        cls.joepublicuser = User.objects.create_user(
            username="joepublic", password="secret"
        )
        cls.nostaffuser = User.objects.create_user(
            username="nostaff", password="secret"
        )
        cls.s1 = Section.objects.create(name="Test section")
        cls.a1 = Article.objects.create(
            content="<p>Middle content</p>",
            date=datetime.datetime(2008, 3, 18, 11, 54, 58),
            section=cls.s1,
            another_section=cls.s1,
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

        # Setup permissions, for our users who can add, change, and delete.
        opts = Article._meta

        # User who can view Articles
        cls.viewuser.user_permissions.add(
            get_perm(Article, get_permission_codename("view", opts))
        )
        # User who can add Articles
        cls.adduser.user_permissions.add(
            get_perm(Article, get_permission_codename("add", opts))
        )
        # User who can change Articles
        cls.changeuser.user_permissions.add(
            get_perm(Article, get_permission_codename("change", opts))
        )
        cls.nostaffuser.user_permissions.add(
            get_perm(Article, get_permission_codename("change", opts))
        )

        # User who can delete Articles
        cls.deleteuser.user_permissions.add(
            get_perm(Article, get_permission_codename("delete", opts))
        )
        cls.deleteuser.user_permissions.add(
            get_perm(Section, get_permission_codename("delete", Section._meta))
        )

        # login POST dicts
        cls.index_url = reverse("admin:index")
        cls.super_login = {
            REDIRECT_FIELD_NAME: cls.index_url,
            "username": "super",
            "password": "secret",
        }
        cls.super_email_login = {
            REDIRECT_FIELD_NAME: cls.index_url,
            "username": "super@example.com",
            "password": "secret",
        }
        cls.super_email_bad_login = {
            REDIRECT_FIELD_NAME: cls.index_url,
            "username": "super@example.com",
            "password": "notsecret",
        }
        cls.adduser_login = {
            REDIRECT_FIELD_NAME: cls.index_url,
            "username": "adduser",
            "password": "secret",
        }
        cls.changeuser_login = {
            REDIRECT_FIELD_NAME: cls.index_url,
            "username": "changeuser",
            "password": "secret",
        }
        cls.deleteuser_login = {
            REDIRECT_FIELD_NAME: cls.index_url,
            "username": "deleteuser",
            "password": "secret",
        }
        cls.nostaff_login = {
            REDIRECT_FIELD_NAME: reverse("has_permission_admin:index"),
            "username": "nostaff",
            "password": "secret",
        }
        cls.joepublic_login = {
            REDIRECT_FIELD_NAME: cls.index_url,
            "username": "joepublic",
            "password": "secret",
        }
        cls.viewuser_login = {
            REDIRECT_FIELD_NAME: cls.index_url,
            "username": "viewuser",
            "password": "secret",
        }
        cls.no_username_login = {
            REDIRECT_FIELD_NAME: cls.index_url,
            "password": "secret",
        }