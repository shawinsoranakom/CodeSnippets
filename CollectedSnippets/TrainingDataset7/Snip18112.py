def test_raise_exception(self):
        class AView(AlwaysFalseView):
            raise_exception = True

        request = self.factory.get("/rand")
        request.user = AnonymousUser()
        with self.assertRaises(PermissionDenied):
            AView.as_view()(request)