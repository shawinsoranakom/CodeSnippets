def setUpTestData(cls):
        # User who can change Reports
        cls.changeuser = User.objects.create_user(
            username="changeuser", password="secret", is_staff=True
        )
        cls.changeuser.user_permissions.add(
            get_perm(Report, get_permission_codename("change", Report._meta))
        )