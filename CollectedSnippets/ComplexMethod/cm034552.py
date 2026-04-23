def generate_report(sources, report_path, coverage_data, target_name, missing):
    output = [
        'Target: %s (%s coverage)' % (target_name, 'missing' if missing else 'exclusive'),
        'GitHub: %stest/integration/targets/%s' % (coverage_data.github_base_url, target_name),
    ]

    for source in sources:
        if source.covered_arcs:
            output.extend([
                '',
                'Source: %s (%d arcs, %d/%d lines):' % (source.path, len(source.covered_arcs), len(source.covered_lines), len(source.lines)),
                'GitHub: %s' % source.github_url,
                '',
            ])
        else:
            output.extend([
                '',
                'Source: %s (%d/%d lines):' % (source.path, len(source.covered_lines), len(source.lines)),
                'GitHub: %s' % source.github_url,
                '',
            ])

        last_line_no = 0

        for line_no, line in enumerate(source.lines, start=1):
            if line_no not in source.covered_lines:
                continue

            if last_line_no and last_line_no != line_no - 1:
                output.append('')

            notes = ''

            if source.covered_arcs:
                from_lines = sorted(p[0] for p in source.covered_points if abs(p[1]) == line_no)
                to_lines = sorted(p[1] for p in source.covered_points if abs(p[0]) == line_no)

                if from_lines:
                    notes += '  ### %s -> (here)' % ', '.join(str(from_line) for from_line in from_lines)

                if to_lines:
                    notes += '  ### (here) -> %s' % ', '.join(str(to_line) for to_line in to_lines)

            output.append('%4d  %s%s' % (line_no, line, notes))
            last_line_no = line_no

    with open(report_path, 'w') as report_file:
        report_file.write('\n'.join(output) + '\n')