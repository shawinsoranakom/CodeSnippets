def test_put_and_delete_rejected(self):
        """
        HTTP PUT and DELETE methods have protection
        """
        req = self._get_request(method="PUT")
        mw = CsrfViewMiddleware(post_form_view)
        with self.assertLogs("django.security.csrf", "WARNING") as cm:
            resp = mw.process_view(req, post_form_view, (), {})
        self.assertForbiddenReason(resp, cm, REASON_NO_CSRF_COOKIE)

        req = self._get_request(method="DELETE")
        with self.assertLogs("django.security.csrf", "WARNING") as cm:
            resp = mw.process_view(req, post_form_view, (), {})
        self.assertForbiddenReason(resp, cm, REASON_NO_CSRF_COOKIE)