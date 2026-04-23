def test_module_name_to_file_path_module(self):
        path = github_links.module_name_to_file_path("django.shortcuts")

        self.assertEqual(last_n_parts(path, 2), "django/shortcuts.py")