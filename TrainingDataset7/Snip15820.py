def test_custom_stderr(self):
        class Command(BaseCommand):
            requires_system_checks = []

            def handle(self, *args, **options):
                self.stderr.write("Hello, World!")

        err = StringIO()
        command = Command(stderr=err)
        call_command(command)
        self.assertEqual(err.getvalue(), "Hello, World!\n")
        err.truncate(0)
        new_err = StringIO()
        call_command(command, stderr=new_err)
        self.assertEqual(err.getvalue(), "")
        self.assertEqual(new_err.getvalue(), "Hello, World!\n")