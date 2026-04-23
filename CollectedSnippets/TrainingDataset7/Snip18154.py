def setUpTestData(cls):
        content_type = ContentType.objects.get_for_model(Group)
        cls.permission = Permission.objects.create(
            name="test",
            content_type=content_type,
            codename="test",
        )
        # User with permission.
        cls.user1 = User.objects.create_user("user 1", "foo@example.com")
        cls.user1.user_permissions.add(cls.permission)
        # User with group permission.
        group1 = Group.objects.create(name="group 1")
        group1.permissions.add(cls.permission)
        group2 = Group.objects.create(name="group 2")
        group2.permissions.add(cls.permission)
        cls.user2 = User.objects.create_user("user 2", "bar@example.com")
        cls.user2.groups.add(group1, group2)
        # Users without permissions.
        cls.user_charlie = User.objects.create_user("charlie", "charlie@example.com")
        cls.user_charlie_b = User.objects.create_user(
            "charliebrown", "charlie@brown.com"
        )
        # Superuser.
        cls.superuser = User.objects.create_superuser(
            "superuser",
            "superuser@example.com",
            "superpassword",
        )
        # Inactive user with permission.
        cls.inactive_user = User.objects.create_user(
            "inactive_user",
            "baz@example.com",
            is_active=False,
        )
        cls.inactive_user.user_permissions.add(cls.permission)