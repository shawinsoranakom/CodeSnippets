def test_callable_object_view(self):
        self.client.force_login(self.superuser)
        response = self.client.head("/xview/callable_object/")
        self.assertEqual(
            response.headers["X-View"], "admin_docs.views.XViewCallableObject"
        )