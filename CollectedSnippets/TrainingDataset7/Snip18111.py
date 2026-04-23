def test_no_redirect_parameter(self):
        class AView(AlwaysFalseView):
            redirect_field_name = None

        self._test_redirect(AView.as_view(), "/accounts/login/")