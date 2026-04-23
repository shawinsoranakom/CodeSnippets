def test_module_name_to_file_path_package(self):
        path = github_links.module_name_to_file_path("django")

        self.assertEqual(last_n_parts(path, 2), "django/__init__.py")