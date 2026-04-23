def test_no_torch_backend_auto_outside_fallback(self):
        lines = INSTALL_SH.read_text().splitlines()
        # Find the fallback block: starts with the "else" after the
        # TORCH_INDEX_URL check and ends at the next "fi".
        fallback_start = None
        fallback_end = None
        for i, line in enumerate(lines):
            if fallback_start is None and "GPU detection failed" in line:
                fallback_start = i
            elif (
                fallback_start is not None
                and fallback_end is None
                and line.strip() == "fi"
            ):
                fallback_end = i
                break
        fallback_range = (
            range(fallback_start or 0, (fallback_end or 0) + 1)
            if fallback_start
            else range(0)
        )

        matches = [
            (i + 1, line)
            for i, line in enumerate(lines)
            if "--torch-backend=auto" in line
            and not line.lstrip().startswith("#")
            and i not in fallback_range
        ]
        assert matches == [], (
            f"install.sh contains --torch-backend=auto outside the fallback block at lines: "
            f"{[m[0] for m in matches]}"
        )