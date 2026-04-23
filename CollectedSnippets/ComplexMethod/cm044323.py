def publish(
    dry_run: bool = False,
    core: bool = False,
    extensions: bool = False,
    openbb: bool = False,
    verbose: bool = False,
    semver: Literal["patch", "minor", "major", "none"] = "patch",
):
    """Publish the Platform to PyPi with optional core or extensions."""
    package_directories = []
    if core:
        package_directories.extend(DIR_CORE)
    if extensions:
        package_directories.extend(DIR_EXTENSIONS)

    partial_run = partial(
        run,
        check=True,
        stdout=None if verbose else PIPE,
        stderr=None if verbose else PIPE,
    )

    for _dir in package_directories:
        is_extension = _dir in DIR_EXTENSIONS
        paths = [
            p
            for p in sorted(DIR_PLATFORM.rglob(f"{_dir}/**/pyproject.toml"))
            if "devtools" not in str(p)
        ]
        total = len(paths)
        logger.info("~~~ /%s ~~~", _dir)
        for i, path in enumerate(paths):
            logger.info(
                "🚀 (%s/%s) Publishing openbb-%s...",
                i + 1,
                total,
                path.parent.stem.replace("_", "-"),
            )
            try:
                # Update openbb-core to latest in each pyproject.toml
                if is_extension:
                    partial_run(
                        [
                            sys.executable,
                            "-m",
                            "poetry",
                            "add",
                            "openbb-core=latest",
                            "--lock",
                        ],
                        cwd=path.parent,
                    )
                # Bump pyproject.toml version
                if semver != "none":
                    partial_run(
                        [sys.executable, "-m", "poetry", "version", semver],
                        cwd=path.parent,
                    )
                # Publish (if not dry running)
                if not dry_run:
                    partial_run(
                        [
                            sys.executable,
                            "-m",
                            "poetry",
                            "publish",
                            "--build",
                        ],
                        cwd=path.parent,
                    )
                logger.info("✅ Success")
            except Exception as e:
                logger.error("❌ Failed to publish %s:\n\n%s", path.parent.stem, e)

    if openbb:
        STEPS = 7
        logger.info("~~~ /openbb ~~~")
        logger.info("🧩 (1/%s) Installing poetry-plugin-up...", STEPS)
        partial_run(
            ["pip", "install", "poetry-plugin-up"],
            cwd=DIR_PLATFORM,
        )
        logger.info("⏫ (2/%s) Updating openbb pyproject.toml...", STEPS)
        partial_run(
            [sys.executable, "-m", "poetry", "up", "--latest"],
            cwd=DIR_PLATFORM,
        )
        logger.info("🔒 (3/%s) Writing openbb poetry.lock...", STEPS)
        partial_run(
            [sys.executable, "-m", "poetry", "up", "--latest"],
            cwd=DIR_PLATFORM,
        )
        logger.info("📍 (4/%s) Installing openbb from /%s...", STEPS, DIR_PLATFORM.stem)
        partial_run(
            ["pip", "install", "-U", "--editable", "."],
            cwd=DIR_PLATFORM,
        )
        logger.info("🚧 (5/%s) Building python interface...", STEPS)
        result = run(
            [sys.executable, "-c", "import openbb; openbb.build()"],  # noqa: S603
            cwd=DIR_PLATFORM,
            check=True,
            capture_output=True,
            text=True,
        )
        if verbose:
            logger.info("Captured result -> %s", result)
        if result.stderr:
            logger.error("❌ stderr is not empty!")
            raise Exception(result.stderr)
        logger.info("🧪 (6/%s) Unit testing...", STEPS)
        partial_run(
            ["pytest", "tests", "-m", "not integration"],
            cwd=DIR_PLATFORM,
        )
        logger.info("🚭 (7/%s) Smoke testing...", STEPS)
        # TODO: Improve smoke test coverage here
        result = run(  # noqa: S603
            [  # noqa: S603
                sys.executable,
                "-c",
                "from openbb import obb; obb.equity.price.historical('AAPL', provider='yfinance')",
            ],
            cwd=DIR_PLATFORM,
            check=True,
            capture_output=True,
            text=True,
        )
        if verbose:
            logger.info("Captured result -> %s", result)
        if result.stderr:
            logger.error("❌ stderr is not empty!")
            raise Exception(result.stderr)
        logger.info("👍 Great success! 👍")
        logger.info(
            "Confirm any files changed and run `poetry publish --build` from /openbb_platform"
        )