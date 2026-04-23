def create_source_sbom() -> None:
    sbom_path = CPYTHON_ROOT_DIR / "Misc/sbom.spdx.json"
    sbom_data = json.loads(sbom_path.read_bytes())

    # We regenerate all of this information. Package information
    # should be preserved though since that is edited by humans.
    sbom_data["files"] = []
    sbom_data["relationships"] = []

    # Ensure all packages in this tool are represented also in the SBOM file.
    actual_names = {package["name"] for package in sbom_data["packages"]}
    expected_names = set(PACKAGE_TO_FILES)
    error_if(
        actual_names != expected_names,
        f"Packages defined in SBOM tool don't match those defined in SBOM file: {actual_names}, {expected_names}",
    )

    check_sbom_packages(sbom_data)

    # We call 'sorted()' here a lot to avoid filesystem scan order issues.
    for name, files in sorted(PACKAGE_TO_FILES.items()):
        package_spdx_id = spdx_id(f"SPDXRef-PACKAGE-{name}")
        exclude = files.exclude or ()
        for include in sorted(files.include or ()):
            # Find all the paths and then filter them through .gitignore.
            paths = glob.glob(include, root_dir=CPYTHON_ROOT_DIR, recursive=True)
            paths = filter_gitignored_paths(paths)
            error_if(
                len(paths) == 0,
                f"No valid paths found at path '{include}' for package '{name}",
            )

            for path in paths:

                # Normalize the filename from any combination of slashes.
                path = str(PurePosixPath(PureWindowsPath(path)))

                # Skip directories and excluded files
                if not (CPYTHON_ROOT_DIR / path).is_file() or path in exclude:
                    continue

                # SPDX requires SHA1 to be used for files, but we provide SHA256 too.
                data = (CPYTHON_ROOT_DIR / path).read_bytes()
                # We normalize line-endings for consistent checksums.
                # This is a rudimentary check for binary files.
                if b"\x00" not in data:
                    data = data.replace(b"\r\n", b"\n")
                checksum_sha1 = hashlib.sha1(data).hexdigest()
                checksum_sha256 = hashlib.sha256(data).hexdigest()

                file_spdx_id = spdx_id(f"SPDXRef-FILE-{path}")
                sbom_data["files"].append({
                    "SPDXID": file_spdx_id,
                    "fileName": path,
                    "checksums": [
                        {"algorithm": "SHA1", "checksumValue": checksum_sha1},
                        {"algorithm": "SHA256", "checksumValue": checksum_sha256},
                    ],
                })

                # Tie each file back to its respective package.
                sbom_data["relationships"].append({
                    "spdxElementId": package_spdx_id,
                    "relatedSpdxElement": file_spdx_id,
                    "relationshipType": "CONTAINS",
                })

    # Update the SBOM on disk
    sbom_path.write_text(json.dumps(sbom_data, indent=2, sort_keys=True))