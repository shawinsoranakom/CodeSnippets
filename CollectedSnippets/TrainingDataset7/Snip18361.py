def test_login_session_without_hash_session_key(self):
        """
        Session without django.contrib.auth.HASH_SESSION_KEY should login
        without an exception.
        """
        user = User.objects.get(username="testclient")
        engine = import_module(settings.SESSION_ENGINE)
        session = engine.SessionStore()
        session[SESSION_KEY] = user.id
        session.save()
        original_session_key = session.session_key
        self.client.cookies[settings.SESSION_COOKIE_NAME] = original_session_key

        self.login()
        self.assertNotEqual(original_session_key, self.client.session.session_key)