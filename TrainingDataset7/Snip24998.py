def test_media_static_dirs_ignored(self):
        """
        Regression test for #23583.
        """
        with override_settings(
            STATIC_ROOT=os.path.join(self.test_dir, "static/"),
            MEDIA_ROOT=os.path.join(self.test_dir, "media_root/"),
        ):
            _, po_contents = self._run_makemessages(domain="djangojs")
            self.assertMsgId(
                "Static content inside app should be included.", po_contents
            )
            self.assertNotMsgId(
                "Content from STATIC_ROOT should not be included", po_contents
            )