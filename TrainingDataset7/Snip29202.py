def test_migrate_to_other_database_with_router(self):
        """Regression test for #16039: migrate with --database option."""
        cts = ContentType.objects.using("other").filter(app_label="multiple_database")

        cts.delete()
        with override_settings(DATABASE_ROUTERS=[SyncOnlyDefaultDatabaseRouter()]):
            management.call_command(
                "migrate", verbosity=0, interactive=False, database="other"
            )

        self.assertEqual(cts.count(), 0)