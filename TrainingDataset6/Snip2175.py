def side_effect(old_cmd, command):
    offending_pattern = re.compile(
        r'(?:Offending (?:key for IP|\S+ key)|Matching host key) in ([^:]+):(\d+)',
        re.MULTILINE)
    offending = offending_pattern.findall(old_cmd.output)
    for filepath, lineno in offending:
        with open(filepath, 'r') as fh:
            lines = fh.readlines()
            del lines[int(lineno) - 1]
        with open(filepath, 'w') as fh:
            fh.writelines(lines)