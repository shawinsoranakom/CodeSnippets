def compare_job_sets(job_set1, job_set2):
    all_job_names = sorted(set(job_set1) | set(job_set2))
    report_lines = []

    for job_name in all_job_names:
        file1 = job_set1.get(job_name)
        file2 = job_set2.get(job_name)

        tests1 = parse_summary_file(file1) if file1 else set()
        tests2 = parse_summary_file(file2) if file2 else set()

        added = tests2 - tests1
        removed = tests1 - tests2

        if added or removed:
            report_lines.append(f"=== Diff for job: {job_name} ===")
            if removed:
                report_lines.append("--- Absent in current run:")
                for test in sorted(removed):
                    report_lines.append(f"    - {test}")
            if added:
                report_lines.append("+++ Appeared in current run:")
                for test in sorted(added):
                    report_lines.append(f"    + {test}")
            report_lines.append("")  # blank line

    return "\n".join(report_lines) if report_lines else "No differences found."