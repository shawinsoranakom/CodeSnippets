def check_python_requirements(path_or_repo_id, requirements_file="requirements.txt", **kwargs):
    """
    Tries to locate `requirements_file` in a local folder or repo, and confirms that the environment has all the
    python dependencies installed.

    Args:
        path_or_repo_id (`str` or `os.PathLike`):
            This can be either:
            - a string, the *model id* of a model repo on huggingface.co.
            - a path to a *directory* potentially containing the file.
        kwargs (`dict[str, Any]`, *optional*):
            Additional arguments to pass to `cached_file`.
    """
    failed = []  # error messages regarding requirements
    try:
        requirements = cached_file(path_or_repo_id=path_or_repo_id, filename=requirements_file, **kwargs)
        with open(requirements, "r") as f:
            requirements = f.readlines()

        for requirement in requirements:
            requirement = requirement.strip()
            if not requirement or requirement.startswith("#"):  # skip empty lines and comments
                continue

            try:
                # e.g. "torch>2.6.0" -> "torch", ">", "2.6.0"
                package_name, delimiter, version_number = split_package_version(requirement)
            except ValueError:  # e.g. "torch", as opposed to "torch>2.6.0"
                package_name = requirement
                delimiter, version_number = None, None

            try:
                local_package_version = importlib.metadata.version(package_name)
            except importlib.metadata.PackageNotFoundError:
                failed.append(f"{requirement} (installed: None)")
                continue

            if delimiter is not None and version_number is not None:
                is_satisfied = VersionComparison.from_string(delimiter).value(
                    version.parse(local_package_version), version.parse(version_number)
                )
            else:
                is_satisfied = True

            if not is_satisfied:
                failed.append(f"{requirement} (installed: {local_package_version})")

    except OSError:  # no requirements.txt
        pass

    if failed:
        raise ImportError(
            f"Missing requirements in your local environment for `{path_or_repo_id}`:\n" + "\n".join(failed)
        )