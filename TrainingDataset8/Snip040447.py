def __init__(self):
        # Whether to prompt to continue on failure or run all
        self.always_continue = False
        # True if Cypress will record videos of our results.
        self.record_results = False
        # True if we're automatically updating snapshots.
        self.update_snapshots = False
        # Parent folder of the specs and scripts.
        # 'e2e' for tests we expect to pass or 'e2e_flaky' for tests with
        # known issues.
        self.tests_dir_name = "e2e"
        # Set to True if any test fails.
        self.any_failed = False
        # Environment variables to pass to Cypress
        self.cypress_env_vars = {}