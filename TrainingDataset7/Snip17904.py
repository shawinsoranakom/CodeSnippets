def test_safe_summary(self):
        msg = self.not_implemented_msg % "a safe_summary"
        with self.assertRaisesMessage(NotImplementedError, msg):
            self.hasher.safe_summary("encoded")