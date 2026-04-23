def test_invalid_backend_type(self):
        msg = "backend must be a dotted import path string (got %r)."
        for backend in (b"auth_tests.CustomModelBackend", object()):
            with self.subTest(backend):
                with self.assertRaisesMessage(TypeError, msg % backend):
                    User.objects.with_perm("auth.test", backend=backend)