def model_failures(self) -> list[dict]:
        # Obtain per-model failures
        def per_model_sum(model_category_dict):
            return dicts_to_sum(model_category_dict["failed"].values())

        failures = {}
        non_model_failures = {
            k: per_model_sum(v) for k, v in self.model_results.items() if sum(per_model_sum(v).values())
        }

        for k, v in self.model_results.items():
            # The keys in `model_results` may contain things like `models_vit` or `quantization_autoawq`
            # Remove the prefix to make the report cleaner.
            k = k.replace("models_", "").replace("quantization_", "")
            if k in NON_MODEL_TEST_MODULES:
                continue

            if sum(per_model_sum(v).values()):
                dict_failed = dict(v["failed"])

                # Model job has a special form for reporting
                if job_name == "run_models_gpu":
                    pytorch_specific_failures = dict_failed.pop("PyTorch")
                    other_failures = dicts_to_sum(dict_failed.values())

                    failures[k] = {
                        "PyTorch": pytorch_specific_failures,
                        "other": other_failures,
                    }

                else:
                    test_name = job_to_test_map[job_name]
                    specific_failures = dict_failed.pop(test_name)
                    failures[k] = {
                        test_name: specific_failures,
                    }

        model_reports = []
        other_module_reports = []

        for key, value in non_model_failures.items():
            key = key.replace("models_", "").replace("quantization_", "")

            if key in NON_MODEL_TEST_MODULES:
                device_report = self.get_device_report(value)

                if sum(value.values()):
                    if device_report:
                        report = f"{device_report}{key}"
                    else:
                        report = key

                    other_module_reports.append(report)

        for key, value in failures.items():
            # Model job has a special form for reporting
            if job_name == "run_models_gpu":
                device_report_values = [
                    value["PyTorch"]["single"],
                    value["PyTorch"]["multi"],
                    sum(value["other"].values()),
                ]

            else:
                test_name = job_to_test_map[job_name]
                device_report_values = [
                    value[test_name]["single"],
                    value[test_name]["multi"],
                ]

            if sum(device_report_values):
                # This is related to `model_header` below
                rjust_width = 9 if job_name == "run_models_gpu" else 6
                device_report = " | ".join([str(x).rjust(rjust_width) for x in device_report_values]) + " | "
                report = f"{device_report}{key}"

                model_reports.append(report)

        # (Possibly truncated) reports for the current workflow run - to be sent to Slack channels
        if job_name == "run_models_gpu":
            model_header = "Single PT |  Multi PT |     Other | Category\n"
        else:
            model_header = "Single |  Multi | Category\n"

        # Used when calling `prepare_reports` below to prepare the `title` argument
        label = test_to_result_name[job_to_test_map[job_name]]

        sorted_model_reports = sorted(model_reports, key=lambda s: s.split("| ")[-1])
        model_failures_report = prepare_reports(
            title=f"These following {label} modules had failures", header=model_header, reports=sorted_model_reports
        )

        module_header = "Single |  Multi | Category\n"
        sorted_module_reports = sorted(other_module_reports, key=lambda s: s.split("| ")[-1])
        module_failures_report = prepare_reports(
            title=f"The following {label} modules had failures", header=module_header, reports=sorted_module_reports
        )

        # To be sent to Slack channels
        model_failure_sections = [{"type": "section", "text": {"type": "mrkdwn", "text": model_failures_report}}]
        model_failure_sections.append({"type": "section", "text": {"type": "mrkdwn", "text": module_failures_report}})

        # Save the complete (i.e. no truncation) failure tables (of the current workflow run)
        # (to be uploaded as artifacts)

        model_failures_report = prepare_reports(
            title=f"These following {label} modules had failures",
            header=model_header,
            reports=sorted_model_reports,
            to_truncate=False,
        )
        file_path = os.path.join(os.getcwd(), f"ci_results_{job_name}/model_failures_report.txt")
        with open(file_path, "w", encoding="UTF-8") as fp:
            fp.write(model_failures_report)

        module_failures_report = prepare_reports(
            title=f"The following {label} modules had failures",
            header=module_header,
            reports=sorted_module_reports,
            to_truncate=False,
        )
        file_path = os.path.join(os.getcwd(), f"ci_results_{job_name}/module_failures_report.txt")
        with open(file_path, "w", encoding="UTF-8") as fp:
            fp.write(module_failures_report)

        if self.prev_ci_artifacts is not None:
            # if the last run produces artifact named `ci_results_{job_name}`
            if (
                f"ci_results_{job_name}" in self.prev_ci_artifacts
                and "model_failures_report.txt" in self.prev_ci_artifacts[f"ci_results_{job_name}"]
            ):
                # Compute the difference of the previous/current (model failure) table
                prev_model_failures = self.prev_ci_artifacts[f"ci_results_{job_name}"]["model_failures_report.txt"]
                entries_changed = self.compute_diff_for_failure_reports(model_failures_report, prev_model_failures)
                if len(entries_changed) > 0:
                    # Save the complete difference
                    diff_report = prepare_reports(
                        title="Changed model modules failures",
                        header=model_header,
                        reports=entries_changed,
                        to_truncate=False,
                    )
                    file_path = os.path.join(os.getcwd(), f"ci_results_{job_name}/changed_model_failures_report.txt")
                    with open(file_path, "w", encoding="UTF-8") as fp:
                        fp.write(diff_report)

                    # To be sent to Slack channels
                    diff_report = prepare_reports(
                        title="*Changed model modules failures*",
                        header=model_header,
                        reports=entries_changed,
                    )
                    model_failure_sections.append(
                        {"type": "section", "text": {"type": "mrkdwn", "text": diff_report}},
                    )

        return model_failure_sections