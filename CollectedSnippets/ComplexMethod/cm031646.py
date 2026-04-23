def main() -> None:
    print("Gathering C API names from docs...")
    names = set()
    for path in C_API_DOCS.glob('**/*.rst'):
        text = path.read_text(encoding="utf-8")
        for name in API_NAME_REGEX.findall(text):
            names.add(name)
    print(f"Got {len(names)} names!")

    print("Scanning for undocumented C API functions...")
    files = [*INCLUDE.iterdir(), *(INCLUDE / "cpython").iterdir()]
    all_missing: list[str] = []
    all_found_ignored: list[str] = []

    for file in files:
        if file.is_dir():
            continue
        assert file.exists()
        text = file.read_text(encoding="utf-8")
        missing, ignored = scan_file_for_docs(str(file.relative_to(INCLUDE)), text, names)
        all_found_ignored += ignored
        all_missing += missing

    fail = False
    to_check = [
        (all_missing, "missing", found_undocumented(len(all_missing) == 1)),
        (
            all_found_ignored,
            "documented but ignored",
            found_ignored_documented(len(all_found_ignored) == 1),
        ),
    ]
    for name_list, what, message in to_check:
        if not name_list:
            continue

        s = "s" if len(name_list) != 1 else ""
        print(f"-- {len(name_list)} {what} C API{s} --")
        for name in name_list:
            print(f" - {name}")
        print(message)
        fail = True

    sys.exit(1 if fail else 0)