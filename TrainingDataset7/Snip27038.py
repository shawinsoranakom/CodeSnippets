def test_showmigrations_unmigrated_app(self):
        out = io.StringIO()
        call_command("showmigrations", "unmigrated_app", stdout=out, no_color=True)
        try:
            self.assertEqual(
                "unmigrated_app\n (no migrations)\n", out.getvalue().lower()
            )
        finally:
            # unmigrated_app.SillyModel has a foreign key to
            # 'migrations.Tribble', but that model is only defined in a
            # migration, so the global app registry never sees it and the
            # reference is left dangling. Remove it to avoid problems in
            # subsequent tests.
            apps._pending_operations.pop(("migrations", "tribble"), None)