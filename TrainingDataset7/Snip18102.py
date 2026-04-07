def test_stacked_mixins_success(self):
        user = models.User.objects.create(username="joe", password="qwerty")
        perms = models.Permission.objects.filter(
            codename__in=("add_customuser", "change_customuser")
        )
        user.user_permissions.add(*perms)
        request = self.factory.get("/rand")
        request.user = user

        view = StackedMixinsView1.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 200)

        view = StackedMixinsView2.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 200)