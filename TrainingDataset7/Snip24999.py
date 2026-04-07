def test_default_root_settings(self):
        """
        Regression test for #23717.
        """
        _, po_contents = self._run_makemessages(domain="djangojs")
        self.assertMsgId("Static content inside app should be included.", po_contents)