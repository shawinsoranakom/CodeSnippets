def teardown_collect_tests(state):
    # Restore the old settings.
    for key, value in state.items():
        setattr(settings, key, value)