def test_process_callback(self):
        """
        #24129 - Tests callback process
        """
        call_args_list = []

        def callback(*args):
            call_args_list.append(args)

        executor = MigrationExecutor(connection, progress_callback=callback)
        # Were the tables there before?
        self.assertTableNotExists("migrations_author")
        self.assertTableNotExists("migrations_tribble")
        executor.migrate(
            [
                ("migrations", "0001_initial"),
                ("migrations", "0002_second"),
            ]
        )
        # Rebuild the graph to reflect the new DB state
        executor.loader.build_graph()

        executor.migrate(
            [
                ("migrations", None),
                ("migrations", None),
            ]
        )
        self.assertTableNotExists("migrations_author")
        self.assertTableNotExists("migrations_tribble")

        migrations = executor.loader.graph.nodes
        expected = [
            ("render_start",),
            ("render_success",),
            ("apply_start", migrations["migrations", "0001_initial"], False),
            ("apply_success", migrations["migrations", "0001_initial"], False),
            ("apply_start", migrations["migrations", "0002_second"], False),
            ("apply_success", migrations["migrations", "0002_second"], False),
            ("render_start",),
            ("render_success",),
            ("unapply_start", migrations["migrations", "0002_second"], False),
            ("unapply_success", migrations["migrations", "0002_second"], False),
            ("unapply_start", migrations["migrations", "0001_initial"], False),
            ("unapply_success", migrations["migrations", "0001_initial"], False),
        ]
        self.assertEqual(call_args_list, expected)