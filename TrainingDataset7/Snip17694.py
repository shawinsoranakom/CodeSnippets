def setUpTestData(cls):
        cls.user_pass = models.User.objects.create(username="joe", password="qwerty")
        cls.user_deny = models.User.objects.create(username="jim", password="qwerty")
        models.Group.objects.create(name="Joe group")
        # Add permissions auth.add_customuser and auth.change_customuser
        perms = models.Permission.objects.filter(
            codename__in=("add_customuser", "change_customuser")
        )
        cls.user_pass.user_permissions.add(*perms)