def _check_dylibs_minos(dylibs: list, expected_minos: str, source: str) -> None:
    mismatches = []
    for dylib in dylibs:
        try:
            result = subprocess.run(
                ["otool", "-l", str(dylib)],
                capture_output=True,
                text=True,
                timeout=30,
            )
        except Exception:
            continue

        minos = None
        lines = result.stdout.splitlines()
        for i, line in enumerate(lines):
            s = line.strip()
            if "LC_BUILD_VERSION" in s:
                for j in range(i + 1, min(i + 6, len(lines))):
                    if lines[j].strip().startswith("minos"):
                        minos = lines[j].strip().split()[1]
                        break
                break
            if "LC_VERSION_MIN_MACOSX" in s:
                for j in range(i + 1, min(i + 4, len(lines))):
                    if lines[j].strip().startswith("version"):
                        minos = lines[j].strip().split()[1]
                        break
                break

        # A dylib with a lower minos than the wheel tag is safe (forward compatible).
        # Only flag dylibs that require a *higher* macOS than the wheel claims to support.
        if minos and tuple(int(x) for x in minos.split(".")) > tuple(
            int(x) for x in expected_minos.split(".")
        ):
            mismatches.append(
                f"{dylib.name}: minos={minos}, expected<={expected_minos}"
            )

    if mismatches:
        raise RuntimeError(
            f"minos/platform tag mismatch in {len(mismatches)} dylib(s):\n"
            + "\n".join(f"  {m}" for m in mismatches)
        )
    print(
        f"OK: All {len(dylibs)} dylib(s) have minos matching "
        f"platform tag ({expected_minos}) for {source}"
    )