def get_changed_lines_for_file(filepath):
    import subprocess
    changed_lines = set()
    try:
        # Get the diff for the file (unified=0 for no context lines)
        diff = subprocess.check_output(
            ['git', 'diff', '--unified=0', 'origin/main...', '--', filepath],
            encoding='utf-8', errors='ignore'
        )
        for line in diff.splitlines():
            if line.startswith('@@'):
                # Example: @@ -10,0 +11,3 @@
                m = re.search(r'\+(\d+)(?:,(\d+))?', line)
                if m:
                    start = int(m.group(1))
                    count = int(m.group(2) or '1')
                    for i in range(start, start + count):
                        changed_lines.add(i)
    except Exception:
        pass
    return changed_lines
