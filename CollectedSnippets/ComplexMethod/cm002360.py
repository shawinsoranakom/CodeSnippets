def category_failures(self) -> dict:
        if job_name != "run_models_gpu":
            category_failures_report = ""
            return {"type": "section", "text": {"type": "mrkdwn", "text": category_failures_report}}

        model_failures = [v["failed"] for v in self.model_results.values()]

        category_failures = {}

        for model_failure in model_failures:
            for key, value in model_failure.items():
                if key not in category_failures:
                    category_failures[key] = dict(value)
                else:
                    category_failures[key]["unclassified"] += value["unclassified"]
                    category_failures[key]["single"] += value["single"]
                    category_failures[key]["multi"] += value["multi"]

        individual_reports = []
        for key, value in category_failures.items():
            device_report = self.get_device_report(value)

            if sum(value.values()):
                if device_report:
                    individual_reports.append(f"{device_report}{key}")
                else:
                    individual_reports.append(key)

        header = "Single |  Multi | Category\n"
        category_failures_report = prepare_reports(
            title="The following categories had failures", header=header, reports=individual_reports
        )

        return {"type": "section", "text": {"type": "mrkdwn", "text": category_failures_report}}