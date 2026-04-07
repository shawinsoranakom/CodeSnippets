def test_single_path(self):
        """
        A Py3.3+ namespace package can be an app if it has only one path.
        """
        with extend_sys_path(self.base_location):
            with self.settings(INSTALLED_APPS=["nsapp"]):
                app_config = apps.get_app_config("nsapp")
                self.assertEqual(app_config.path, self.app_path)