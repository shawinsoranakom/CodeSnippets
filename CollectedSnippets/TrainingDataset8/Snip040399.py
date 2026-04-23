def main():
    git_files = sorted(
        subprocess.check_output(["git", "ls-files", "--no-empty-directory"])
        .decode()
        .strip()
        .splitlines()
    )

    invalid_files_count = 0
    for fileloc in git_files:
        if IGNORE_PATTERN.search(fileloc):
            continue
        filepath = Path(fileloc)
        # Exclude submodules
        if not filepath.is_file():
            continue

        try:
            file_content = filepath.read_text()
            if LICENSE_TEXT not in file_content:
                print("Found file without license header", fileloc)
                invalid_files_count += 1
        except:
            print(
                f"Failed to open the file: {fileloc}. Is it binary file?",
            )
            invalid_files_count += 1

    print("Invalid files count:", invalid_files_count)
    if invalid_files_count > 0:
        sys.exit(1)