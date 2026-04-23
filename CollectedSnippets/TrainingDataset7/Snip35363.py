def tearDownClass(Cls):
        # override to avoid a second cls._rollback_atomics() which would fail.
        # Normal setUpClass() methods won't have exception handling so this
        # method wouldn't typically be run.
        pass