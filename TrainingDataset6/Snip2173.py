def match(command):
    if not command.script:
        return False
    if not command.script.startswith(commands):
        return False

    patterns = (
        r'WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!',
        r'WARNING: POSSIBLE DNS SPOOFING DETECTED!',
        r"Warning: the \S+ host key for '([^']+)' differs from the key for the IP address '([^']+)'",
    )

    return any(re.findall(pattern, command.output) for pattern in patterns)