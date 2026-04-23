def test_custom_redirect_url(self):
        class AView(AlwaysFalseView):
            login_url = "/login/"

        self._test_redirect(AView.as_view(), "/login/?next=/rand")