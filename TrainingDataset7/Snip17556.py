def test_raises_exception(self):
        msg = (
            "No authentication backends have been defined. "
            "Does AUTHENTICATION_BACKENDS contain anything?"
        )
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            self.user.has_perm(("perm", TestObj()))