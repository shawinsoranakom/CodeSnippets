def main():
    """Main function"""
    files_missing_both = []
    files_missing_copyright = []
    files_missing_license = []

    for file_path in sys.argv[1:]:
        status = check_spdx_header_status(file_path)

        if status == SPDXStatus.MISSING_BOTH:
            files_missing_both.append(file_path)
        elif status == SPDXStatus.MISSING_COPYRIGHT:
            files_missing_copyright.append(file_path)
        elif status == SPDXStatus.MISSING_LICENSE:
            files_missing_license.append(file_path)
        else:
            continue

    # Collect all files that need fixing
    all_files_to_fix = (
        files_missing_both + files_missing_copyright + files_missing_license
    )
    if all_files_to_fix:
        print("The following files are missing the SPDX header:")
        if files_missing_both:
            for file_path in files_missing_both:
                print(f"  {file_path}")
                add_header(file_path, SPDXStatus.MISSING_BOTH)

        if files_missing_copyright:
            for file_path in files_missing_copyright:
                print(f"  {file_path}")
                add_header(file_path, SPDXStatus.MISSING_COPYRIGHT)
        if files_missing_license:
            for file_path in files_missing_license:
                print(f"  {file_path}")
                add_header(file_path, SPDXStatus.MISSING_LICENSE)

    sys.exit(1 if all_files_to_fix else 0)