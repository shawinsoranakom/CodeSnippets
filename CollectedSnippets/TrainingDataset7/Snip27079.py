def test_makemigrations_consistency_checks_respect_routers(self):
        """
        The history consistency checks in makemigrations respect
        settings.DATABASE_ROUTERS.
        """

        def patched_has_table(migration_recorder):
            if migration_recorder.connection is connections["other"]:
                raise Exception("Other connection")
            else:
                return mock.DEFAULT

        self.assertTableNotExists("migrations_unicodemodel")
        apps.register_model("migrations", UnicodeModel)
        with mock.patch.object(
            MigrationRecorder, "has_table", autospec=True, side_effect=patched_has_table
        ) as has_table:
            with self.temporary_migration_module() as migration_dir:
                call_command("makemigrations", "migrations", verbosity=0)
                initial_file = os.path.join(migration_dir, "0001_initial.py")
                self.assertTrue(os.path.exists(initial_file))
                self.assertEqual(has_table.call_count, 1)  # 'default' is checked

                # Router says not to migrate 'other' so consistency shouldn't
                # be checked.
                with self.settings(DATABASE_ROUTERS=["migrations.routers.TestRouter"]):
                    call_command("makemigrations", "migrations", verbosity=0)
                self.assertEqual(has_table.call_count, 2)  # 'default' again

                # With a router that doesn't prohibit migrating 'other',
                # consistency is checked.
                with self.settings(
                    DATABASE_ROUTERS=["migrations.routers.DefaultOtherRouter"]
                ):
                    with self.assertRaisesMessage(Exception, "Other connection"):
                        call_command("makemigrations", "migrations", verbosity=0)
                self.assertEqual(has_table.call_count, 4)  # 'default' and 'other'

                # With a router that doesn't allow migrating on any database,
                # no consistency checks are made.
                with self.settings(DATABASE_ROUTERS=["migrations.routers.TestRouter"]):
                    with mock.patch.object(
                        TestRouter, "allow_migrate", return_value=False
                    ) as allow_migrate:
                        call_command("makemigrations", "migrations", verbosity=0)
                allow_migrate.assert_any_call(
                    "other", "migrations", model_name="UnicodeModel"
                )
                # allow_migrate() is called with the correct arguments.
                self.assertGreater(len(allow_migrate.mock_calls), 0)
                called_aliases = set()
                for mock_call in allow_migrate.mock_calls:
                    _, call_args, call_kwargs = mock_call
                    connection_alias, app_name = call_args
                    called_aliases.add(connection_alias)
                    # Raises an error if invalid app_name/model_name occurs.
                    apps.get_app_config(app_name).get_model(call_kwargs["model_name"])
                self.assertEqual(called_aliases, set(connections))
                self.assertEqual(has_table.call_count, 4)