def setUpClass(cls):
        # The file implementing the code under test is in the docs folder and
        # is not part of the Django package. This means it cannot be imported
        # through standard means. Include its parent in the pythonpath for the
        # duration of the tests to allow the code to be imported.
        cls.ext_path = str((pathlib.Path(__file__).parents[2] / "docs/_ext").resolve())
        sys.path.insert(0, cls.ext_path)
        cls.addClassCleanup(sys.path.remove, cls.ext_path)
        cls.addClassCleanup(sys.modules.pop, "github_links", None)
        # Linters/IDEs may not be able to detect this as a valid import.
        import github_links as _github_links

        global github_links
        github_links = _github_links