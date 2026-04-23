def get_new_failures(self, prev_ci_artifacts, include_all=False):
        """
        Get new model failures compared to previous CI artifacts.

        Args:
            prev_ci_artifacts: Previous CI artifacts to compare against
            include_all: If True, include all failures without checking prev_ci_artifacts

        Returns:
            Dictionary with new failures, or empty dict if no failures
        """
        if prev_ci_artifacts is None:
            # Not compare against a previous run
            return {}

        # Get target results
        if len(self.model_results) > 0:
            target_results = self.model_results
        else:
            target_results = self.additional_results[job_to_test_map[job_name]]

        # Make the format uniform between `model_results` and `additional_results[XXX]`
        if "failures" in target_results:
            target_results = {job_name: target_results}
        sorted_dict = sorted(target_results.items(), key=lambda t: t[0])

        # Get previous model results
        prev_results = {}
        if not include_all and prev_ci_artifacts is not None:
            job = job_to_test_map[job_name]
            if (
                f"ci_results_{job_name}" in prev_ci_artifacts
                and f"{test_to_result_name[job]}_results.json" in prev_ci_artifacts[f"ci_results_{job_name}"]
            ):
                prev_results = json.loads(
                    prev_ci_artifacts[f"ci_results_{job_name}"][f"{test_to_result_name[job]}_results.json"]
                )
                # Make the format uniform between `model_results` and `additional_results[XXX]`
                if "failures" in prev_results:
                    prev_results = {job_name: prev_results}

        # Extract new failures
        new_failures = {}
        for job, job_result in sorted_dict:
            # Skip if no failures in current results
            if "failures" not in job_result or not job_result["failures"]:
                continue

            # Get previous failures for this model (if exists)
            prev_failures = {}
            if not include_all and job in prev_results:
                prev_model_data = prev_results[job]
                if "failures" in prev_model_data:
                    prev_failures = prev_model_data["failures"]

            # Build set of previous failure lines for quick lookup by device type
            prev_failure_lines = {}
            if not include_all:
                for device_type, failures_list in prev_failures.items():
                    if isinstance(failures_list, list):
                        prev_failure_lines[device_type] = {f["line"] for f in failures_list if "line" in f}

            # Check each device type (single, multi)
            job_new_failures = {}
            for device_type, failures_list in job_result["failures"].items():
                if not isinstance(failures_list, list):
                    continue

                # Filter to only new failures
                new_failures_for_device = []
                for failure in failures_list:
                    if "line" not in failure:
                        continue

                    # Include if flag is set, or if not in previous results
                    if (
                        include_all
                        or device_type not in prev_failure_lines
                        or failure["line"] not in prev_failure_lines[device_type]
                    ):
                        new_failures_for_device.append(failure)

                # Only add device type if there are new failures
                if new_failures_for_device:
                    job_new_failures[f"{device_type}-gpu"] = new_failures_for_device

            # Only add model if there are new failures
            if job_new_failures:
                job = job.replace("models_", "").replace("quantization_", "")
                new_failures[job] = {"failures": job_new_failures}
                # Add job_link if it exists
                if "job_link" in job_result:
                    new_failures[job]["job_link"] = job_result["job_link"]

        return new_failures