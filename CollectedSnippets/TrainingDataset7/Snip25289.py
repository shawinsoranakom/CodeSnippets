def dummy_allow_migrate(db, app_label, **hints):
    # Prevent checks from being run on the 'other' database, which doesn't have
    # its check_field() method mocked in the test.
    return db == "default"