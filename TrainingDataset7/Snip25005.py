def test_media_static_dirs_ignored(self):
        with override_settings(
            STATIC_ROOT=os.path.join(self.test_dir, "static/"),
            MEDIA_ROOT=os.path.join(self.test_dir, "media_root/"),
        ):
            out, _ = self._run_makemessages()
            self.assertIn("ignoring directory static", out)
            self.assertIn("ignoring directory media_root", out)