def setUpTestData(cls):
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
        # Setup permissions.
        opts = UserProxy._meta
        cls.viewuser.user_permissions.add(
            get_perm(UserProxy, get_permission_codename("view", opts))
        )
        cls.adduser.user_permissions.add(
            get_perm(UserProxy, get_permission_codename("add", opts))
        )
        cls.changeuser.user_permissions.add(
            get_perm(UserProxy, get_permission_codename("change", opts))
        )
        cls.deleteuser.user_permissions.add(
            get_perm(UserProxy, get_permission_codename("delete", opts))
        )
        # UserProxy instances.
        cls.user_proxy = UserProxy.objects.create(
            username="user_proxy", password="secret"
        )