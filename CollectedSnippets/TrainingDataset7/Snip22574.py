def test_recursive(self):
        f = FilePathField(path=self.path, recursive=True, match=r"^.*?\.py$")
        expected = [
            ("/filepathfield_test_dir/__init__.py", "__init__.py"),
            ("/filepathfield_test_dir/a.py", "a.py"),
            ("/filepathfield_test_dir/ab.py", "ab.py"),
            ("/filepathfield_test_dir/b.py", "b.py"),
            ("/filepathfield_test_dir/c/__init__.py", "c/__init__.py"),
            ("/filepathfield_test_dir/c/d.py", "c/d.py"),
            ("/filepathfield_test_dir/c/e.py", "c/e.py"),
            ("/filepathfield_test_dir/c/f/__init__.py", "c/f/__init__.py"),
            ("/filepathfield_test_dir/c/f/g.py", "c/f/g.py"),
            ("/filepathfield_test_dir/h/__init__.py", "h/__init__.py"),
            ("/filepathfield_test_dir/j/__init__.py", "j/__init__.py"),
        ]
        self.assertChoices(f, expected)