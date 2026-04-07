def test_delete_str_in_model_admin(self):
        """
        Test if the admin delete page shows the correct string representation
        for a proxy model.
        """
        user = TrackerUser.objects.get(name="Django Pony")
        proxy = ProxyTrackerUser.objects.get(name="Django Pony")

        user_str = 'Tracker user: <a href="%s">%s</a>' % (
            reverse("admin_proxy:proxy_models_trackeruser_change", args=(user.pk,)),
            user,
        )
        proxy_str = 'Proxy tracker user: <a href="%s">%s</a>' % (
            reverse(
                "admin_proxy:proxy_models_proxytrackeruser_change", args=(proxy.pk,)
            ),
            proxy,
        )

        self.client.force_login(self.superuser)
        response = self.client.get(
            reverse("admin_proxy:proxy_models_trackeruser_delete", args=(user.pk,))
        )
        delete_str = response.context["deleted_objects"][0]
        self.assertEqual(delete_str, user_str)
        response = self.client.get(
            reverse(
                "admin_proxy:proxy_models_proxytrackeruser_delete", args=(proxy.pk,)
            )
        )
        delete_str = response.context["deleted_objects"][0]
        self.assertEqual(delete_str, proxy_str)