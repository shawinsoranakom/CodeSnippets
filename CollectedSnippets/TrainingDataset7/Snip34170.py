def test_template_dirs_ignore_empty_path(self):
        self.assertEqual(autoreload.get_template_directories(), set())