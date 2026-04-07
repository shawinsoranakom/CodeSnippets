def test_detect_soft_applied_add_field_manytomanyfield(self):
        """
        executor.detect_soft_applied() detects ManyToManyField tables from an
        AddField operation. This checks the case of AddField in a migration
        with other operations (0001) and the case of AddField in its own
        migration (0002).
        """
        tables = [
            # from 0001
            "migrations_project",
            "migrations_task",
            "migrations_project_tasks",
            # from 0002
            "migrations_task_projects",
        ]
        executor = MigrationExecutor(connection)
        # Create the tables for 0001 but make it look like the migration hasn't
        # been applied.
        executor.migrate([("migrations", "0001_initial")])
        executor.migrate([("migrations", None)], fake=True)
        for table in tables[:3]:
            self.assertTableExists(table)
        # Table detection sees 0001 is applied but not 0002.
        migration = executor.loader.get_migration("migrations", "0001_initial")
        self.assertIs(executor.detect_soft_applied(None, migration)[0], True)
        migration = executor.loader.get_migration("migrations", "0002_initial")
        self.assertIs(executor.detect_soft_applied(None, migration)[0], False)

        # Create the tables for both migrations but make it look like neither
        # has been applied.
        executor.loader.build_graph()
        executor.migrate([("migrations", "0001_initial")], fake=True)
        executor.migrate([("migrations", "0002_initial")])
        executor.loader.build_graph()
        executor.migrate([("migrations", None)], fake=True)
        # Table detection sees 0002 is applied.
        migration = executor.loader.get_migration("migrations", "0002_initial")
        self.assertIs(executor.detect_soft_applied(None, migration)[0], True)

        # Leave the tables for 0001 except the many-to-many table. That missing
        # table should cause detect_soft_applied() to return False.
        with connection.schema_editor() as editor:
            for table in tables[2:]:
                editor.execute(editor.sql_delete_table % {"table": table})
        migration = executor.loader.get_migration("migrations", "0001_initial")
        self.assertIs(executor.detect_soft_applied(None, migration)[0], False)

        # Cleanup by removing the remaining tables.
        with connection.schema_editor() as editor:
            for table in tables[:2]:
                editor.execute(editor.sql_delete_table % {"table": table})
        for table in tables:
            self.assertTableNotExists(table)