def test_script_prefix_set_in_commands(self):
        self.write_settings(
            "settings.py",
            apps=["user_commands"],
            sdict={
                "ROOT_URLCONF": '"user_commands.urls"',
                "FORCE_SCRIPT_NAME": '"/PREFIX/"',
            },
        )
        out, err = self.run_manage(["reverse_url"])
        self.assertNoOutput(err)
        self.assertEqual(out.strip(), "/PREFIX/some/url/")