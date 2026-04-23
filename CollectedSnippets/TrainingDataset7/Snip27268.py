def test_loading_order_does_not_create_circular_dependency(self):
        """
        Before, for these migrations:
        app1
        [ ] 0001_squashed_initial <- replaces app1.0001
        [ ] 0002_squashed_initial <- replaces app1.0001
            depends on app1.0001_squashed_initial & app2.0001_squashed_initial
        app2
        [ ] 0001_squashed_initial <- replaces app2.0001

        When loading app1's migrations, if 0002_squashed_initial was first:
        {'0002_squashed_initial', '0001_initial', '0001_squashed_initial'}
        Then CircularDependencyError was raised, but it's resolvable as:
        {'0001_initial', '0001_squashed_initial', '0002_squashed_initial'}
        """
        # Create a test settings file to provide to the subprocess.
        MIGRATION_MODULES = {
            "app1": "migrations.test_migrations_squashed_replaced_order.app1",
            "app2": "migrations.test_migrations_squashed_replaced_order.app2",
        }
        INSTALLED_APPS = [
            "migrations.test_migrations_squashed_replaced_order.app1",
            "migrations.test_migrations_squashed_replaced_order.app2",
        ]
        tests_dir = Path(__file__).parent.parent
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".py", dir=tests_dir, delete=False
        ) as test_settings:
            self.addCleanup(os.remove, test_settings.name)
            for attr, value in settings._wrapped.__dict__.items():
                # Only write builtin values so that any settings that reference
                # a value that needs an import are omitted.
                if attr.isupper() and type(value).__module__ == "builtins":
                    test_settings.write(f"{attr} = {value!r}\n")
            # Provide overrides here, instead of via decorators.
            test_settings.write(f"DATABASES = {settings.DATABASES}\n")
            test_settings.write(f"MIGRATION_MODULES = {MIGRATION_MODULES}\n")
            # Isolate away other test apps.
            test_settings.write(
                "INSTALLED_APPS=[a for a in INSTALLED_APPS if a.startswith('django')]\n"
            )
            test_settings.write(f"INSTALLED_APPS += {INSTALLED_APPS}\n")

        test_environ = os.environ.copy()
        test_python_path = sys.path.copy()
        test_python_path.append(str(tests_dir))
        test_environ["PYTHONPATH"] = os.pathsep.join(test_python_path)
        # Ensure deterministic failures.
        test_environ["PYTHONHASHSEED"] = "1"

        args = [
            sys.executable,
            "-m",
            "django",
            "showmigrations",
            "app1",
            "--skip-checks",
            "--settings",
            Path(test_settings.name).stem,
        ]
        try:
            subprocess.run(
                args, capture_output=True, env=test_environ, check=True, text=True
            )
        except subprocess.CalledProcessError as err:
            self.fail(err.stderr)