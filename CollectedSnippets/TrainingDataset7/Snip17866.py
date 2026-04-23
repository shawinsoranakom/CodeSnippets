def test_invalid_password(self):
        msg = "Password must be a string or bytes, got int."
        with self.assertRaisesMessage(TypeError, msg):
            make_password(1)