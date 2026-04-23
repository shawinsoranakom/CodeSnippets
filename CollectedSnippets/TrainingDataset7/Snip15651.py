def run_test(self, args, settings_file=None, apps=None, umask=-1):
        base_dir = os.path.dirname(self.test_dir)
        # The base dir for Django's tests is one level up.
        tests_dir = os.path.dirname(os.path.dirname(__file__))
        # The base dir for Django is one level above the test dir. We don't use
        # `import django` to figure that out, so we don't pick up a Django
        # from site-packages or similar.
        django_dir = os.path.dirname(tests_dir)
        ext_backend_base_dirs = self._ext_backend_paths()

        # Define a temporary environment for the subprocess
        test_environ = os.environ.copy()

        # Set the test environment
        if settings_file:
            test_environ["DJANGO_SETTINGS_MODULE"] = settings_file
        elif "DJANGO_SETTINGS_MODULE" in test_environ:
            del test_environ["DJANGO_SETTINGS_MODULE"]
        python_path = [base_dir, django_dir, tests_dir]
        python_path.extend(ext_backend_base_dirs)
        test_environ["PYTHONPATH"] = os.pathsep.join(python_path)
        test_environ["PYTHONWARNINGS"] = ""
        test_environ["PYTHON_COLORS"] = "0"

        p = subprocess.run(
            [sys.executable, *args],
            capture_output=True,
            cwd=self.test_dir,
            env=test_environ,
            text=True,
            umask=umask,
        )
        return p.stdout, p.stderr