def __init__(
        self,
        title: str,
        ci_title: str,
        model_results: dict,
        additional_results: dict,
        selected_warnings: list | None = None,
        prev_ci_artifacts=None,
        other_ci_artifacts=None,
    ):
        self.title = title
        self.ci_title = ci_title

        # Failures and success of the modeling tests
        self.n_model_success = sum(r["success"] for r in model_results.values())
        self.n_model_single_gpu_failures = sum(dicts_to_sum(r["failed"])["single"] for r in model_results.values())
        self.n_model_multi_gpu_failures = sum(dicts_to_sum(r["failed"])["multi"] for r in model_results.values())

        # Some suites do not have a distinction between single and multi GPU.
        self.n_model_unknown_failures = sum(dicts_to_sum(r["failed"])["unclassified"] for r in model_results.values())
        self.n_model_failures = (
            self.n_model_single_gpu_failures + self.n_model_multi_gpu_failures + self.n_model_unknown_failures
        )
        self.n_model_jobs_errored_out = sum(r["error"] for r in model_results.values())

        # Failures and success of the additional tests
        self.n_additional_success = sum(r["success"] for r in additional_results.values())
        self.n_additional_jobs_errored_out = sum(r["error"] for r in additional_results.values())

        if len(additional_results) > 0:
            # `dicts_to_sum` uses `dicts_to_sum` which requires a non empty dictionary. Let's just add an empty entry.
            all_additional_failures = dicts_to_sum([r["failed"] for r in additional_results.values()])
            self.n_additional_single_gpu_failures = all_additional_failures["single"]
            self.n_additional_multi_gpu_failures = all_additional_failures["multi"]
            self.n_additional_unknown_gpu_failures = all_additional_failures["unclassified"]
        else:
            self.n_additional_single_gpu_failures = 0
            self.n_additional_multi_gpu_failures = 0
            self.n_additional_unknown_gpu_failures = 0

        self.n_additional_failures = (
            self.n_additional_single_gpu_failures
            + self.n_additional_multi_gpu_failures
            + self.n_additional_unknown_gpu_failures
        )

        # Results
        self.n_failures = self.n_model_failures + self.n_additional_failures
        self.n_success = self.n_model_success + self.n_additional_success
        self.n_tests = self.n_failures + self.n_success
        self.n_jobs_errored_out = self.n_model_jobs_errored_out + self.n_additional_jobs_errored_out

        self.model_results = model_results
        self.additional_results = additional_results

        self.thread_ts = None

        if selected_warnings is None:
            selected_warnings = []
        self.selected_warnings = selected_warnings

        self.prev_ci_artifacts = prev_ci_artifacts
        self.other_ci_artifacts = other_ci_artifacts