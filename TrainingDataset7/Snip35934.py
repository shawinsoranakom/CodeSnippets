def test_discover_commands_in_eggs(self):
        """
        Management commands can also be loaded from Python eggs.
        """
        egg_dir = "%s/eggs" % os.path.dirname(__file__)
        egg_name = "%s/basic.egg" % egg_dir
        with extend_sys_path(egg_name):
            with self.settings(INSTALLED_APPS=["commandegg"]):
                cmds = find_commands(
                    os.path.join(apps.get_app_config("commandegg").path, "management")
                )
        self.assertEqual(cmds, ["eggcommand"])