def test_backend_uses_deferred_annotations(self):
        class AnnotatedBackend:
            invariant_user = self.user1

            def authenticate(
                self,
                request: HttpRequest,
                username: AnnotatedUsername,
                password: AnnotatedPassword,
            ) -> User | None:
                return self.invariant_user

        with unittest.mock.patch(
            "django.contrib.auth.import_string", return_value=AnnotatedBackend
        ):
            self.assertEqual(authenticate(username="test", password="test"), self.user1)