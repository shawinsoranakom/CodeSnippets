def test_raise_exception_custom_message(self):
        msg = "You don't have access here"

        class AView(AlwaysFalseView):
            raise_exception = True
            permission_denied_message = msg

        request = self.factory.get("/rand")
        request.user = AnonymousUser()
        view = AView.as_view()
        with self.assertRaisesMessage(PermissionDenied, msg):
            view(request)