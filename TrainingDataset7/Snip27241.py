def test_has_table_cached(self):
        """
        The has_table() method caches a positive result and not continually
        query for the existence of the migrations table.
        """
        recorder = MigrationRecorder(connection)
        self.assertIs(recorder.has_table(), True)
        with self.assertNumQueries(0):
            self.assertIs(recorder.has_table(), True)