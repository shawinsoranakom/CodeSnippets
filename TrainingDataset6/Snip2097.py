def _getavailable_lifecycles(command):
    return re.search(
        r'Available lifecycle phases are: (.+) -> \[Help 1\]', command.output)