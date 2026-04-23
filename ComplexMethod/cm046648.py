def _find_blocked_commands(command: str) -> set[str]:
    """Detect blocked commands using shlex tokenization and regex scanning.

    Catches: full paths (/usr/bin/sudo), quoted strings ("sudo"),
    split-quotes (su""do), backslash escapes (\\rm), and command-position
    words after ;, |, &&, $().
    """
    blocked = set()

    # 1. shlex tokenization (handles quotes, escapes, concatenation)
    try:
        tokens = (
            shlex.split(command)
            if sys.platform != "win32"
            else shlex.split(command, posix = False)
        )
    except ValueError:
        tokens = command.split()

    for token in tokens:
        base = os.path.basename(token).lower()
        # Strip common Windows executable extensions so that
        # runas.exe, shutdown.bat, etc. match the blocklist.
        stem, ext = os.path.splitext(base)
        if ext in {".exe", ".com", ".bat", ".cmd"}:
            base = stem
        if base in _BLOCKED_COMMANDS:
            blocked.add(base)

    # 2. Regex: catch blocked words at shell command boundaries
    #    (semicolons, pipes, &&, ||, backticks, $(), <(), subshells, newlines)
    #    Uses a single combined pattern for all blocked words.
    #    Handles optional Unix path prefix (/usr/bin/) and Windows drive
    #    letter prefix (C:\Windows\...\).
    lowered = command.lower()
    if _BLOCKED_COMMANDS:
        words_alt = "|".join(re.escape(w) for w in sorted(_BLOCKED_COMMANDS))
        pattern = (
            rf"(?:^|[;&|`\n(]\s*|[$]\(\s*|<\(\s*)"
            rf"(?:[\w./\\-]*/|[a-zA-Z]:[/\\][\w./\\-]*)?"
            rf"({words_alt})(?:\.(?:exe|com|bat|cmd))?\b"
        )
        blocked.update(re.findall(pattern, lowered))

    # 3. Check for nested shell invocations (bash -c 'sudo whoami',
    #    bash -lc '...', bash --login -c '...', cmd /c '...').
    #    When a -c or /c flag is found, look backwards for a shell name
    #    (skipping intermediate flags like --login, -l, -x) and recursively
    #    scan the nested command string.
    _SHELLS = {"bash", "sh", "zsh", "dash", "ksh", "csh", "tcsh", "fish"}
    _SHELLS_WIN = {"cmd", "cmd.exe"}
    for i, token in enumerate(tokens):
        tok_lower = token.lower()
        # Match -c exactly, or combined flags ending in c (e.g. -lc, -xc)
        is_unix_c = tok_lower == "-c" or (
            tok_lower.startswith("-")
            and tok_lower.endswith("c")
            and not tok_lower.startswith("--")
        )
        is_win_c = tok_lower == "/c"
        if not (is_unix_c or is_win_c) or i < 1 or i + 1 >= len(tokens):
            continue
        # Look backwards past any flags to find the shell binary.
        # On Unix, flags start with - (skip those). On Windows, flags
        # start with / but so do absolute paths, so only skip short
        # single-char /X flags (not /bin/bash style paths).
        for j in range(i - 1, -1, -1):
            prev = tokens[j]
            if prev.startswith("-"):
                continue  # skip Unix flags like --login, -l
            if is_win_c and prev.startswith("/") and len(prev) <= 3:
                continue  # skip Windows flags like /s, /q (not /bin/bash)
            prev_base = os.path.basename(prev).lower()
            if is_unix_c and prev_base in _SHELLS:
                blocked |= _find_blocked_commands(tokens[i + 1])
            elif is_win_c and prev_base in _SHELLS_WIN:
                blocked |= _find_blocked_commands(tokens[i + 1])
            break  # stop at first non-flag token

    return blocked