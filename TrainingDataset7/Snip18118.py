def setUpTestData(cls):
        cls.user = models.User.objects.create(username="joe", password="qwerty")
        perms = models.Permission.objects.filter(
            codename__in=("add_customuser", "change_customuser")
        )
        cls.user.user_permissions.add(*perms)