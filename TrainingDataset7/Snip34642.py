def test_session_engine_is_invalid(self):
        with self.assertRaisesMessage(ImportError, "nonexistent"):
            self.test_session_modifying_view()