def test_stacked_mixins_missing_permission(self):
        user = models.User.objects.create(username="joe", password="qwerty")
        perms = models.Permission.objects.filter(codename__in=("add_customuser",))
        user.user_permissions.add(*perms)
        request = self.factory.get("/rand")
        request.user = user

        view = StackedMixinsView1.as_view()
        with self.assertRaises(PermissionDenied):
            view(request)

        view = StackedMixinsView2.as_view()
        with self.assertRaises(PermissionDenied):
            view(request)