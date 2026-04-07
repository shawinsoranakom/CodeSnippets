def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(
            username="super", password="secret", email="super@example.com"
        )
        content_type = ContentType.objects.get_for_model(Band)
        Permission.objects.create(
            name="custom", codename="custom_band", content_type=content_type
        )
        for user_type in ("view", "add", "change", "delete", "custom"):
            username = "%suser" % user_type
            user = User.objects.create_user(
                username=username, password="secret", is_staff=True
            )
            permission = Permission.objects.get(
                codename="%s_band" % user_type, content_type=content_type
            )
            user.user_permissions.add(permission)
            setattr(cls, username, user)