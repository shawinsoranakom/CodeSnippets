def get_torch_version(sha: str | None = None) -> str:
    """Determine the torch version string.

    The version is determined from one of the following sources, in order of
    precedence:
    1. The PYTORCH_BUILD_VERSION and PYTORCH_BUILD_NUMBER environment variables.
       These are set by the PyTorch build system when building official
       releases. If built from an sdist, it is checked that the version matches
       the sdist version.
    2. The PKG-INFO file, if it exists. This file is included in source
       distributions (sdist) and contains the version of the sdist.
    3. The version.txt file, which contains the base version string. If the git
       commit SHA is available, it is appended to the version string to
       indicate that this is a development build.
    """
    pytorch_root = Path(__file__).absolute().parent.parent
    pkg_info_path = pytorch_root / "PKG-INFO"
    if pkg_info_path.exists():
        with open(pkg_info_path) as f:
            pkg_info = email.message_from_file(f)
        sdist_version = pkg_info["Version"]
    else:
        sdist_version = None
    if os.getenv("PYTORCH_BUILD_VERSION"):
        if os.getenv("PYTORCH_BUILD_NUMBER") is None:
            raise AssertionError(
                "PYTORCH_BUILD_NUMBER must be set when PYTORCH_BUILD_VERSION is set"
            )
        build_number = int(os.getenv("PYTORCH_BUILD_NUMBER", ""))
        version = os.getenv("PYTORCH_BUILD_VERSION", "")
        if build_number > 1:
            version += ".post" + str(build_number)
        origin = "PYTORCH_BUILD_{VERSION,NUMBER} env variables"
    elif sdist_version:
        version = sdist_version
        origin = "PKG-INFO"
    else:
        version = Path(pytorch_root / "version.txt").read_text().strip()
        origin = "version.txt"
        if sdist_version is None and sha != UNKNOWN:
            if sha is None:
                sha = get_sha(pytorch_root)
            version += "+git" + sha[:7]
            origin += " and git commit"
    # Validate that the version is PEP 440 compliant
    parsed_version = Version(version)
    if sdist_version:
        if (l := parsed_version.local) and l.startswith("git"):
            # Assume local version is git<sha> and
            # hence whole version is source version
            source_version = version
        else:
            # local version is absent or platform tag
            source_version = version.partition("+")[0]
        if sdist_version != source_version:
            raise AssertionError(
                f"Source part '{source_version}' of version '{version}' from "
                f"{origin} does not match version '{sdist_version}' from PKG-INFO"
            )
    return version