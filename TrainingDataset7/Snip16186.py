def test_has_view_or_change_permission_required(self):
        """
        Users require the change permission for the related model to the
        autocomplete view for it.
        """
        request = self.factory.get(self.url, {"term": "is", **self.opts})
        request.user = self.user
        with self.assertRaises(PermissionDenied):
            AutocompleteJsonView.as_view(**self.as_view_args)(request)
        for permission in ("view", "change"):
            with self.subTest(permission=permission):
                self.user.user_permissions.clear()
                p = Permission.objects.get(
                    content_type=ContentType.objects.get_for_model(Question),
                    codename="%s_question" % permission,
                )
                self.user.user_permissions.add(p)
                request.user = User.objects.get(pk=self.user.pk)
                response = AutocompleteJsonView.as_view(**self.as_view_args)(request)
                self.assertEqual(response.status_code, 200)