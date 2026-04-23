def payload(self) -> str:
        blocks = [self.header]

        if self.ci_title:
            blocks.append(self.ci_title_section)

        if self.n_model_failures > 0 or self.n_additional_failures > 0 or self.n_jobs_errored_out > 0:
            blocks.append(self.failures)

        if self.n_model_failures > 0:
            block = self.category_failures
            if block["text"]["text"]:
                blocks.append(block)

            for block in self.model_failures:
                if block["text"]["text"]:
                    blocks.append(block)

        if self.n_additional_failures > 0:
            blocks.append(self.additional_failures)

        if self.n_model_failures == 0 and self.n_additional_failures == 0:
            blocks.append(self.no_failures)

        if len(self.selected_warnings) > 0:
            blocks.append(self.warnings)

        for idx, (prev_workflow_run_id, prev_ci_artifacts) in enumerate(
            [self.prev_ci_artifacts] + self.other_ci_artifacts
        ):
            # `include_all` is `True` when the CI is running on a pull request, so it treats all failing tests
            # in the current CI run as "new failing tests". The `utils/check_bad_commit.py`, run in a later job,
            # will analyze the scenario in depth, in particular if a failing test in the current run is a new
            # failing test, or already failed before but with the same/different failing reason.
            include_all = os.environ.get("GITHUB_EVENT_NAME") in ["issue_comment", "pull_request"]
            if include_all and prev_ci_artifacts is None:
                prev_ci_artifacts = {}
            new_failures = self.get_new_failures(prev_ci_artifacts=prev_ci_artifacts)
            if new_failures:
                filename = "new_failures"
                if idx > 0:
                    filename = f"{filename}_against_{prev_workflow_run_id}"

                file_path = os.path.join(os.getcwd(), f"ci_results_{job_name}/{filename}.json")
                with open(file_path, "w", encoding="UTF-8") as fp:
                    json.dump(new_failures, fp, ensure_ascii=False, indent=4)

                # upload results to Hub dataset
                file_path = os.path.join(os.getcwd(), f"ci_results_{job_name}/{filename}.json")
                commit_info = api.upload_file(
                    path_or_fileobj=file_path,
                    path_in_repo=f"{report_repo_folder}/ci_results_{job_name}/{filename}.json",
                    repo_id=report_repo_id,
                    repo_type="dataset",
                    token=os.environ.get("TRANSFORMERS_CI_RESULTS_UPLOAD_TOKEN", None),
                )
                new_failures_url = f"https://huggingface.co/datasets/{report_repo_id}/raw/{commit_info.oid}/{report_repo_folder}/ci_results_{job_name}/{filename}.json"

                nb_new_failed_tests = 0
                for results in new_failures.values():
                    if "failures" in results:
                        for failures_list in results["failures"].values():
                            nb_new_failed_tests += len(failures_list)

                if idx == 0:
                    block = {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*There are {nb_new_failed_tests} new failed tests*\n\n(compared to previous run: <https://github.com/huggingface/transformers/actions/runs/{prev_workflow_run_id}|{prev_workflow_run_id}>)",
                        },
                        "accessory": {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Check new failures"},
                            "url": new_failures_url,
                        },
                    }
                    blocks.append(block)
                else:
                    block = {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            # TODO: We should NOT assume it's always Nvidia CI, but it's the case at this moment.
                            "text": f"*There are {nb_new_failed_tests} failed tests unique to this run*\n\n(compared to{' Nvidia CI ' if is_scheduled_ci_run else ' '}run: <https://github.com/huggingface/transformers/actions/runs/{prev_workflow_run_id}|{prev_workflow_run_id}>)",
                        },
                        "accessory": {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Check failures"},
                            "url": new_failures_url,
                        },
                    }
                    blocks.append(block)

        if diff_file_url is not None:
            block = {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Test results diff*\n\n(compared to previous run: <https://github.com/huggingface/transformers/actions/runs/{prev_workflow_run_id}|{prev_workflow_run_id}>)",
                },
                "accessory": {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Check test result diff file"},
                    "url": diff_file_url,
                },
            }
            blocks.append(block)

        return json.dumps(blocks)