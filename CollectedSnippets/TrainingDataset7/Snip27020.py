def test_migrate_with_custom_system_checks(self):
        original_checks = registry.registered_checks.copy()

        @register(Tags.signals)
        def my_check(app_configs, **kwargs):
            return [Error("my error")]

        self.addCleanup(setattr, registry, "registered_checks", original_checks)

        class CustomMigrateCommandWithSignalsChecks(MigrateCommand):
            requires_system_checks = [Tags.signals]

        command = CustomMigrateCommandWithSignalsChecks()
        with self.assertRaises(SystemCheckError):
            call_command(command, skip_checks=False, stderr=io.StringIO())

        class CustomMigrateCommandWithSecurityChecks(MigrateCommand):
            requires_system_checks = [Tags.security]

        command = CustomMigrateCommandWithSecurityChecks()
        call_command(command, skip_checks=False, stdout=io.StringIO())