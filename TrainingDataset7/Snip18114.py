def test_raise_exception_custom_message_function(self):
        msg = "You don't have access here"

        class AView(AlwaysFalseView):
            raise_exception = True

            def get_permission_denied_message(self):
                return msg

        request = self.factory.get("/rand")
        request.user = AnonymousUser()
        view = AView.as_view()
        with self.assertRaisesMessage(PermissionDenied, msg):
            view(request)