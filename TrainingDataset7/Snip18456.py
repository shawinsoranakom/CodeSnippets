def test_release_memory_without_garbage_collection(self):
        # Schedule the restore of the garbage collection settings.
        self.addCleanup(gc.set_debug, 0)
        self.addCleanup(gc.enable)

        # Disable automatic garbage collection to control when it's triggered,
        # then run a full collection cycle to ensure `gc.garbage` is empty.
        gc.disable()
        gc.collect()

        # The garbage list isn't automatically populated to avoid CPU overhead,
        # so debugging needs to be enabled to track all unreachable items and
        # have them stored in `gc.garbage`.
        gc.set_debug(gc.DEBUG_SAVEALL)

        # Create a new connection that will be closed during the test, and also
        # ensure that a `DatabaseErrorWrapper` is created for this connection.
        test_connection = connection.copy()
        with test_connection.wrap_database_errors:
            self.assertEqual(test_connection.queries, [])

        # Close the connection and remove references to it. This will mark all
        # objects related to the connection as garbage to be collected.
        test_connection.close()
        test_connection = None

        # Enforce garbage collection to populate `gc.garbage` for inspection.
        gc.collect()
        self.assertEqual(gc.garbage, [])