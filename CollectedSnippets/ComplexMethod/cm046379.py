def check_requirements(requirements=ROOT.parent / "requirements.txt", exclude=(), install=True, cmds=""):
    """Check if installed dependencies meet Ultralytics YOLO models requirements and attempt to auto-update if needed.

    Args:
        requirements (Path | str | list[str|tuple] | tuple[str]): Path to a requirements.txt file, a single package
            requirement as a string, a list of package requirements as strings, or a list containing strings and tuples
            of interchangeable packages.
        exclude (tuple): Tuple of package names to exclude from checking.
        install (bool): If True, attempt to auto-update packages that don't meet requirements.
        cmds (str): Additional commands to pass to the pip install command when auto-updating.

    Examples:
        >>> from ultralytics.utils.checks import check_requirements

        Check a requirements.txt file
        >>> check_requirements("path/to/requirements.txt")

        Check a single package
        >>> check_requirements("ultralytics>=8.3.200", cmds="--index-url https://download.pytorch.org/whl/cpu")

        Check multiple packages
        >>> check_requirements(["numpy", "ultralytics"])

        Check with interchangeable packages
        >>> check_requirements([("onnxruntime", "onnxruntime-gpu"), "numpy"])
    """
    prefix = colorstr("red", "bold", "requirements:")

    if os.environ.get("ULTRALYTICS_SKIP_REQUIREMENTS_CHECKS", "0") == "1":
        LOGGER.info(f"{prefix} ULTRALYTICS_SKIP_REQUIREMENTS_CHECKS=1 detected, skipping requirements check.")
        return True

    if isinstance(requirements, Path):  # requirements.txt file
        file = requirements.resolve()
        assert file.exists(), f"{prefix} {file} not found, check failed."
        requirements = [f"{x.name}{x.specifier}" for x in parse_requirements(file) if x.name not in exclude]
    elif isinstance(requirements, str):
        requirements = [requirements]

    pkgs = []
    for r in requirements:
        candidates = r if isinstance(r, (list, tuple)) else [r]
        satisfied = False

        for candidate in candidates:
            r_stripped = candidate.rpartition("/")[-1].replace(".git", "")  # replace git+https://org/repo.git -> 'repo'
            match = re.match(r"([a-zA-Z0-9-_]+)([<>!=~]+.*)?", r_stripped)
            name, required = match[1], match[2].strip() if match[2] else ""
            try:
                if check_version(metadata.version(name), required):
                    satisfied = True
                    break
            except (AssertionError, metadata.PackageNotFoundError):
                continue

        if not satisfied:
            pkg = candidates[0]
            if "git+" in pkg:  # strip version constraints from git URLs for pip
                url, sep, marker = pkg.partition(";")
                pkg = re.sub(r"[<>!=~]+.*$", "", url) + sep + marker
            pkgs.append(pkg)

    @Retry(times=2, delay=1)
    def attempt_install(packages, commands, use_uv):
        """Attempt package installation with uv if available, falling back to pip."""
        if use_uv:
            # Use --python to explicitly target current interpreter (venv or system)
            # This ensures correct installation when VIRTUAL_ENV env var isn't set
            return subprocess.check_output(
                f'uv pip install --no-cache-dir --python "{sys.executable}" {packages} {commands} '
                f"--index-strategy=unsafe-best-match --break-system-packages",
                shell=True,
                stderr=subprocess.STDOUT,
                text=True,
            )
        return subprocess.check_output(
            f'"{sys.executable}" -m pip install --no-cache-dir {packages} {commands}',
            shell=True,
            stderr=subprocess.STDOUT,
            text=True,
        )

    s = " ".join(f'"{x}"' for x in pkgs)  # console string
    if s:
        if install and AUTOINSTALL:  # check environment variable
            # Note uv fails on arm64 macOS and Raspberry Pi runners
            n = len(pkgs)  # number of packages updates
            LOGGER.info(f"{prefix} Ultralytics requirement{'s' * (n > 1)} {pkgs} not found, attempting AutoUpdate...")
            try:
                t = time.time()
                assert ONLINE, "AutoUpdate skipped (offline)"
                use_uv = not ARM64 and check_uv()  # uv fails on ARM64
                LOGGER.info(attempt_install(s, cmds, use_uv=use_uv))
                dt = time.time() - t
                LOGGER.info(f"{prefix} AutoUpdate success ✅ {dt:.1f}s")
                LOGGER.warning(
                    f"{prefix} {colorstr('bold', 'Restart runtime or rerun command for updates to take effect')}\n"
                )
            except Exception as e:
                msg = f"{prefix} ❌ {e}"
                if hasattr(e, "output") and e.output:
                    msg += f"\n{e.output}"
                LOGGER.warning(msg)
                return False
        else:
            return False

    return True