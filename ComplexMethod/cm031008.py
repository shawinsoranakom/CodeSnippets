def get_exitcode(self, fail_env_changed: bool, fail_rerun: bool) -> int:
        exitcode = 0
        if self.bad:
            exitcode = EXITCODE_BAD_TEST
        elif self.interrupted:
            exitcode = EXITCODE_INTERRUPTED
        elif fail_env_changed and self.env_changed:
            exitcode = EXITCODE_ENV_CHANGED
        elif self.no_tests_run():
            exitcode = EXITCODE_NO_TESTS_RAN
        elif fail_rerun and self.rerun:
            exitcode = EXITCODE_RERUN_FAIL
        elif self.worker_bug:
            exitcode = EXITCODE_BAD_TEST
        return exitcode