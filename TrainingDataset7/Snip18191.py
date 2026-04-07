async def test_csrf_validation_passes_after_process_request_login_async(self):
        """See test_csrf_validation_passes_after_process_request_login."""
        csrf_client = AsyncClient(enforce_csrf_checks=True)
        csrf_secret = _get_new_csrf_string()
        csrf_token = _mask_cipher_secret(csrf_secret)
        csrf_token_form = _mask_cipher_secret(csrf_secret)
        headers = {self.header: "fakeuser"}
        data = {"csrfmiddlewaretoken": csrf_token_form}

        # Verify that CSRF is configured for the view
        csrf_client.cookies.load({settings.CSRF_COOKIE_NAME: csrf_token})
        response = await csrf_client.post("/remote_user/", **headers)
        self.assertEqual(response.status_code, 403)
        self.assertIn(b"CSRF verification failed.", response.content)

        # This request will call django.contrib.auth.alogin() which will call
        # django.middleware.csrf.rotate_token() thus changing the value of
        # request.META['CSRF_COOKIE'] from the user submitted value set by
        # CsrfViewMiddleware.process_request() to the new csrftoken value set
        # by rotate_token(). Csrf validation should still pass when the view is
        # later processed by CsrfViewMiddleware.process_view()
        csrf_client.cookies.load({settings.CSRF_COOKIE_NAME: csrf_token})
        response = await csrf_client.post("/remote_user/", data, **headers)
        self.assertEqual(response.status_code, 200)