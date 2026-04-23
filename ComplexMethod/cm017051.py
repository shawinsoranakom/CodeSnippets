def generate_docs_src_versions_for_file(file_path: Path) -> None:
    target_versions = ["py39", "py310"]
    full_path_str = str(file_path)
    for target_version in target_versions:
        if f"_{target_version}" in full_path_str:
            logging.info(
                f"Skipping {file_path}, already a version file for {target_version}"
            )
            return
    base_content = file_path.read_text(encoding="utf-8")
    previous_content = {base_content}
    for target_version in target_versions:
        version_result = subprocess.run(
            [
                find_ruff_bin(),
                "check",
                "--target-version",
                target_version,
                "--fix",
                "--unsafe-fixes",
                "-",
            ],
            input=base_content.encode("utf-8"),
            capture_output=True,
        )
        content_target = version_result.stdout.decode("utf-8")
        format_result = subprocess.run(
            [find_ruff_bin(), "format", "-"],
            input=content_target.encode("utf-8"),
            capture_output=True,
        )
        content_format = format_result.stdout.decode("utf-8")
        if content_format in previous_content:
            continue
        previous_content.add(content_format)
        # Determine where the version label should go: in the parent directory
        # name or in the file name, matching the source structure.
        label_in_parent = False
        for v in target_versions:
            if f"_{v}" in file_path.parent.name:
                label_in_parent = True
                break
        if label_in_parent:
            parent_name = file_path.parent.name
            for v in target_versions:
                parent_name = parent_name.replace(f"_{v}", "")
            new_parent = file_path.parent.parent / f"{parent_name}_{target_version}"
            new_parent.mkdir(parents=True, exist_ok=True)
            version_file = new_parent / file_path.name
        else:
            base_name = file_path.stem
            for v in target_versions:
                if base_name.endswith(f"_{v}"):
                    base_name = base_name[: -len(f"_{v}")]
                    break
            version_file = file_path.with_name(f"{base_name}_{target_version}.py")
        logging.info(f"Writing to {version_file}")
        version_file.write_text(content_format, encoding="utf-8")