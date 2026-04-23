def find_tcmalloc() -> Path | None:
    try:
        # get all shared libs the dynamic loader knows about
        output = subprocess.check_output(
            ["ldconfig", "-p"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return None

    # search for libtcmalloc and libtcmalloc_minimal
    for library_pattern in (
        r"\blibtcmalloc_minimal\.so\.(\d+)\b",
        r"\blibtcmalloc\.so\.(\d+)\b",
    ):
        candidates: list[tuple[int, Path]] = []
        for line in output.splitlines():
            match = re.search(library_pattern, line)
            if match is None or "=>" not in line:
                continue
            candidate = Path(line.split("=>")[1].strip())
            if candidate.exists():
                candidates.append((int(match.group(1)), candidate))

        if candidates:
            # if multiple candidates are found, pick the one with the highest
            # version number
            return max(candidates, key=lambda item: item[0])[1]

    return None