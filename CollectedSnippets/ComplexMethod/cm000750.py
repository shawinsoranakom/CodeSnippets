async def run(
        self,
        input_data: Input,
        *,
        credentials: GithubCredentials,
        **kwargs,
    ) -> BlockOutput:

        try:
            target = int(input_data.target)
        except ValueError:
            target = input_data.target

        result = await self.get_ci_results(
            credentials,
            input_data.repo,
            target,
            input_data.search_pattern,
            input_data.check_name_filter,
        )

        check_runs = result["check_runs"]

        # Calculate overall status
        if not check_runs:
            yield "overall_status", "no_checks"
            yield "overall_conclusion", "no_checks"
        else:
            all_completed = all(run["status"] == "completed" for run in check_runs)
            if all_completed:
                yield "overall_status", "completed"
                # Determine overall conclusion
                has_failure = any(
                    run["conclusion"] in ["failure", "timed_out", "action_required"]
                    for run in check_runs
                )
                if has_failure:
                    yield "overall_conclusion", "failure"
                else:
                    yield "overall_conclusion", "success"
            else:
                yield "overall_status", "pending"
                yield "overall_conclusion", "pending"

        # Count checks
        total = len(check_runs)
        passed = sum(1 for run in check_runs if run.get("conclusion") == "success")
        failed = sum(
            1 for run in check_runs if run.get("conclusion") in ["failure", "timed_out"]
        )

        yield "total_checks", total
        yield "passed_checks", passed
        yield "failed_checks", failed

        # Output check runs
        yield "check_runs", check_runs

        # Search for patterns if specified
        if input_data.search_pattern:
            matched_lines = await self.search_in_logs(
                check_runs, input_data.search_pattern
            )
            if matched_lines:
                yield "matched_lines", matched_lines