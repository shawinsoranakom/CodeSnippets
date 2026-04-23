def patch_close_connection(creation):
        # If DatabaseCreation.destroy_test_db() closes the database connection,
        # that behavior must be disabled to prevent each test from crashing.
        if close_method_name := creation.destroy_test_db_connection_close_method:
            setattr(creation.connection, close_method_name, mock.Mock())