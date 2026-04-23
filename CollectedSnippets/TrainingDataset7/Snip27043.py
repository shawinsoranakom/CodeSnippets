def test_showmigrations_plan_app_label_no_migrations(self):
        out = io.StringIO()
        call_command(
            "showmigrations", "unmigrated_app", format="plan", stdout=out, no_color=True
        )
        try:
            self.assertEqual("(no migrations)\n", out.getvalue())
        finally:
            # unmigrated_app.SillyModel has a foreign key to
            # 'migrations.Tribble', but that model is only defined in a
            # migration, so the global app registry never sees it and the
            # reference is left dangling. Remove it to avoid problems in
            # subsequent tests.
            apps._pending_operations.pop(("migrations", "tribble"), None)