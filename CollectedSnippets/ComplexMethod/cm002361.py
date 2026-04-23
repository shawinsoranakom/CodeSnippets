def compute_diff_for_failure_reports(self, curr_failure_report, prev_failure_report):  # noqa
        # Remove the leading and training parts that don't contain failure count information.
        model_failures = curr_failure_report.split("\n")[3:-2]
        prev_model_failures = prev_failure_report.split("\n")[3:-2]
        entries_changed = set(model_failures).difference(prev_model_failures)

        prev_map = {}
        for f in prev_model_failures:
            items = [x.strip() for x in f.split("| ")]
            prev_map[items[-1]] = [int(x) for x in items[:-1]]

        curr_map = {}
        for f in entries_changed:
            items = [x.strip() for x in f.split("| ")]
            curr_map[items[-1]] = [int(x) for x in items[:-1]]

        diff_map = {}
        for k, v in curr_map.items():
            if k not in prev_map:
                diff_map[k] = v
            else:
                diff = [x - y for x, y in zip(v, prev_map[k])]
                if max(diff) > 0:
                    diff_map[k] = diff

        entries_changed = []
        for model_name, diff_values in diff_map.items():
            diff = [str(x) for x in diff_values]
            diff = [f"+{x}" if (x != "0" and not x.startswith("-")) else x for x in diff]
            diff = [x.rjust(9) for x in diff]
            device_report = " | ".join(diff) + " | "
            report = f"{device_report}{model_name}"
            entries_changed.append(report)
        entries_changed = sorted(entries_changed, key=lambda s: s.split("| ")[-1])

        return entries_changed