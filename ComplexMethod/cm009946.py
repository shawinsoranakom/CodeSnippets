def get_nightly_git_hash(version: str) -> str:
    """Download a nightly wheel and extract the git hash from its version.py file."""
    # Extract variant from version to construct correct URL
    variant = extract_variant_from_version(version)
    nightly_index_url = f"https://download.pytorch.org/whl/nightly/{variant}/"

    torch_version_spec = f"torch=={version}"

    # Create a temporary directory for downloading
    with tempfile.TemporaryDirectory(prefix="pytorch-hash-extract-") as temp_dir:
        temp_path = Path(temp_dir)

        # Download the wheel
        report(f"-- Downloading {version} wheel to extract git hash...")
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

        result = subprocess.run(download_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(
                f"Failed to download {version} wheel for git hash extraction: {result.stderr}"
            )

        # Find the downloaded wheel file
        wheel_files = list(temp_path.glob("torch-*.whl"))
        if not wheel_files:
            raise RuntimeError(f"No torch wheel found after downloading {version}")

        wheel_file = wheel_files[0]

        # Extract the wheel and look for version.py
        with tempfile.TemporaryDirectory(
            prefix="pytorch-wheel-extract-"
        ) as extract_dir:
            extract_path = Path(extract_dir)

            with zipfile.ZipFile(wheel_file, "r") as zip_ref:
                zip_ref.extractall(extract_path)

            # Find torch directory and version.py
            torch_dirs = list(extract_path.glob("torch"))
            if not torch_dirs:
                torch_dirs = list(extract_path.glob("*/torch"))

            if not torch_dirs:
                raise RuntimeError(f"Could not find torch directory in {version} wheel")

            version_file = torch_dirs[0] / "version.py"
            if not version_file.exists():
                raise RuntimeError(f"Could not find version.py in {version} wheel")

            # Read and parse version.py to extract git_version (nightly branch commit)
            from ast import literal_eval

            nightly_commit = None
            with version_file.open(encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith("git_version"):
                        try:
                            # Parse the git_version assignment, e.g., git_version = "abc123def456"
                            nightly_commit = literal_eval(
                                line.partition("=")[2].strip()
                            )
                            break
                        except (ValueError, SyntaxError):
                            continue

            if not nightly_commit:
                raise RuntimeError(
                    f"Could not parse git_version from {version} wheel's version.py"
                )

            # Now fetch the nightly branch and extract the real source commit from the message
            report("-- Fetching nightly branch to extract source commit...")

            # Fetch only the nightly branch
            subprocess.check_call(["git", "fetch", "origin", "nightly"], cwd=str(CWD))

            # Get the commit message from the nightly commit
            commit_message = subprocess.check_output(
                ["git", "show", "--no-patch", "--format=%s", nightly_commit],
                cwd=str(CWD),
                text=True,
            ).strip()

            # Parse the commit message to extract the real hash
            # Format: "2025-08-06 nightly release (74a754aae98aabc2aca67e5edb41cc684fae9a82)"
            import re

            hash_match = re.search(r"\(([0-9a-fA-F]{40})\)", commit_message)
            if hash_match:
                real_commit = hash_match.group(1)
                report(f"-- Extracted source commit: {real_commit[:12]}...")
                return real_commit
            else:
                raise RuntimeError(
                    f"Could not parse commit hash from nightly commit message: {commit_message}"
                )