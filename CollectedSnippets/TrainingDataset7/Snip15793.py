def test_custom_system_checks(self):
        original_checks = registry.registered_checks.copy()

        @register(Tags.signals)
        def my_check(app_configs, **kwargs):
            return [Error("my error")]

        class CustomException(Exception):
            pass

        self.addCleanup(setattr, registry, "registered_checks", original_checks)

        class CustomRunserverCommand(RunserverCommand):
            """
            Rather than mock run(), raise immediately after system checks run.
            """

            def check_migrations(self, *args, **kwargs):
                raise CustomException

        class CustomRunserverCommandWithSignalsChecks(CustomRunserverCommand):
            requires_system_checks = [Tags.signals]

        command = CustomRunserverCommandWithSignalsChecks()
        with self.assertRaises(SystemCheckError):
            call_command(
                command,
                use_reloader=False,
                skip_checks=False,
                stdout=StringIO(),
                stderr=StringIO(),
            )

        class CustomMigrateCommandWithSecurityChecks(CustomRunserverCommand):
            requires_system_checks = [Tags.security]

        command = CustomMigrateCommandWithSecurityChecks()
        with self.assertRaises(CustomException):
            call_command(
                command,
                use_reloader=False,
                skip_checks=False,
                stdout=StringIO(),
                stderr=StringIO(),
            )