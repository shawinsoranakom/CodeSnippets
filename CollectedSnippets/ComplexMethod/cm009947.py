def download_and_extract_nightly_wheel(version: str) -> None:
    """Download and extract nightly PyTorch wheel for USE_NIGHTLY=VERSION builds."""

    # Extract variant from version (e.g., cpu, cu121, cu118, rocm6.2)
    variant = extract_variant_from_version(version)
    nightly_index_url = f"https://download.pytorch.org/whl/nightly/{variant}/"

    # Construct the full torch version spec
    torch_version_spec = f"torch=={version}"

    # Create a temporary directory for downloading
    with tempfile.TemporaryDirectory(prefix="pytorch-nightly-") as temp_dir:
        temp_path = Path(temp_dir)

        # Use pip to download the specific nightly wheel
        download_cmd = [
            "uvx",
            "pip",
            "download",
            "--index-url",
            nightly_index_url,
            "--pre",
            "--no-deps",
            "--dest",
            str(temp_path),
            torch_version_spec,
        ]

        report("-- Downloading nightly PyTorch wheel...")
        result = subprocess.run(download_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            # Try to get the latest nightly version for the same variant to help the user
            variant = extract_variant_from_version(version)
            try:
                report(f"-- Detecting latest {variant} nightly version...")
                latest_version = get_latest_nightly_version(variant)
                error_msg = f"Failed to download nightly wheel for version {version}: {result.stderr.strip()}"
                error_msg += (
                    f"\n\nLatest available {variant} nightly version: {latest_version}"
                )
                error_msg += f'\nTry: USE_NIGHTLY="{latest_version}"'

                # Also get the git hash for the latest version
                git_hash = get_nightly_git_hash(latest_version)
                error_msg += f"\n\nIMPORTANT: You must checkout the matching source commit:\ngit checkout {git_hash}"
            except Exception:
                # If we can't get latest for this variant, try CPU as fallback
                try:
                    report("-- Detecting latest CPU nightly version...")
                    latest_version = get_latest_nightly_version("cpu")
                    error_msg = f"Failed to download nightly wheel for version {version}: {result.stderr.strip()}"
                    error_msg += f"\n\nCould not find {variant} nightlies. Latest available CPU nightly version: {latest_version}"
                    error_msg += f'\nTry: USE_NIGHTLY="{latest_version}"'
                except Exception:
                    error_msg = f"Failed to download nightly wheel for version {version}: {result.stderr.strip()}"
                    error_msg += "\n\nCould not determine latest nightly version. "
                    error_msg += "Check https://download.pytorch.org/whl/nightly/ for available versions."

            raise RuntimeError(error_msg)

        # Find the downloaded wheel file
        wheel_files = list(temp_path.glob("torch-*.whl"))
        if not wheel_files:
            raise RuntimeError("No torch wheel found after download")
        elif len(wheel_files) > 1:
            raise RuntimeError(f"Multiple torch wheels found: {wheel_files}")

        wheel_file = wheel_files[0]
        report(f"-- Downloaded wheel: {wheel_file.name}")

        # Extract the wheel
        with tempfile.TemporaryDirectory(
            prefix="pytorch-wheel-extract-"
        ) as extract_dir:
            extract_path = Path(extract_dir)

            # Use Python's zipfile to extract the wheel
            with zipfile.ZipFile(wheel_file, "r") as zip_ref:
                zip_ref.extractall(extract_path)

            # Find the torch directory in the extracted wheel
            torch_dirs = list(extract_path.glob("torch"))
            if not torch_dirs:
                # Sometimes the torch directory might be nested
                torch_dirs = list(extract_path.glob("*/torch"))

            if not torch_dirs:
                raise RuntimeError("Could not find torch directory in extracted wheel")

            source_torch_dir = torch_dirs[0]
            target_torch_dir = TORCH_DIR

            report(
                f"-- Extracting wheel contents from {source_torch_dir} to {target_torch_dir}"
            )

            # Copy the essential files from the wheel to our local directory
            # Based on the file listing logic from tools/nightly.py
            files_to_copy: list[Path] = []

            # Get platform-specific binary files
            if IS_LINUX:
                files_to_copy.extend(source_torch_dir.glob("*.so"))
                files_to_copy.extend(
                    (source_torch_dir / "lib").glob("*.so*")
                    if (source_torch_dir / "lib").exists()
                    else []
                )
            elif IS_DARWIN:
                files_to_copy.extend(source_torch_dir.glob("*.so"))
                files_to_copy.extend(
                    (source_torch_dir / "lib").glob("*.dylib")
                    if (source_torch_dir / "lib").exists()
                    else []
                )
            elif IS_WINDOWS:
                files_to_copy.extend(source_torch_dir.glob("*.pyd"))
                files_to_copy.extend(
                    (source_torch_dir / "lib").glob("*.lib")
                    if (source_torch_dir / "lib").exists()
                    else []
                )
                files_to_copy.extend(
                    (source_torch_dir / "lib").glob("*.dll")
                    if (source_torch_dir / "lib").exists()
                    else []
                )

            # Add essential directories and files
            essential_items = ["version.py", "bin", "include", "lib"]
            for item_name in essential_items:
                item_path = source_torch_dir / item_name
                if item_path.exists():
                    files_to_copy.append(item_path)

            # Add testing internal generated files
            testing_generated = source_torch_dir / "testing" / "_internal" / "generated"
            if testing_generated.exists():
                files_to_copy.append(testing_generated)

            # Copy all the files and directories
            for src_path in files_to_copy:
                rel_path = src_path.relative_to(source_torch_dir)
                dst_path = target_torch_dir / rel_path

                # Copy files and directories, preserving existing subdirectories
                if src_path.is_dir():
                    # Create destination directory if it doesn't exist
                    dst_path.mkdir(parents=True, exist_ok=True)
                    # Copy individual entries from source directory
                    for src_item in src_path.iterdir():
                        dst_item = dst_path / src_item.name
                        if src_item.is_dir():
                            # Recursively copy subdirectories (this will preserve existing ones)
                            shutil.copytree(src_item, dst_item, dirs_exist_ok=True)
                        else:
                            # Copy individual files, overwriting existing ones
                            shutil.copy2(src_item, dst_item)
                else:
                    # For files, remove existing and copy new
                    if dst_path.exists():
                        dst_path.unlink()
                    dst_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_path, dst_path)

                report(f"   Copied {rel_path}")

    report("-- Nightly wheel extraction completed")