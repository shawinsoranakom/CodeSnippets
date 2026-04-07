def test_custom_redirect_parameter(self):
        class AView(AlwaysFalseView):
            redirect_field_name = "goto"

        self._test_redirect(AView.as_view(), "/accounts/login/?goto=/rand")