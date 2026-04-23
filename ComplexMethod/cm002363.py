def additional_failures(self) -> dict:
        failures = {k: v["failed"] for k, v in self.additional_results.items()}
        errors = {k: v["error"] for k, v in self.additional_results.items()}

        individual_reports = []
        for key, value in failures.items():
            device_report = self.get_device_report(value)

            if sum(value.values()) or errors[key]:
                report = f"{key}"
                if errors[key]:
                    report = f"[Errored out] {report}"
                if device_report:
                    report = f"{device_report}{report}"

                individual_reports.append(report)

        header = "Single |  Multi | Category\n"
        failures_report = prepare_reports(
            title="The following non-modeling tests had failures", header=header, reports=individual_reports
        )

        return {"type": "section", "text": {"type": "mrkdwn", "text": failures_report}}