def build_triton(
    *,
    version: str,
    commit_hash: str,
    device: str = "cuda",
    py_version: str | None = None,
    release: bool = False,
    with_clang_ldd: bool = False,
) -> Path:
    env = os.environ.copy()
    if "MAX_JOBS" not in env:
        max_jobs = os.cpu_count() or 1
        env["MAX_JOBS"] = str(max_jobs)

    with TemporaryDirectory() as tmpdir:
        triton_basedir = Path(tmpdir) / "triton"
        triton_pythondir = triton_basedir / "python"

        triton_repo = "https://github.com/openai/triton"
        if device == "rocm":
            triton_pkg_name = "triton-rocm"
        elif device == "xpu":
            triton_pkg_name = "triton-xpu"
            triton_repo = "https://github.com/intel/intel-xpu-backend-for-triton"
        else:
            triton_pkg_name = "triton"
        check_call(["git", "clone", triton_repo, "triton"], cwd=tmpdir)
        if release:
            ver, rev, patch = version.split(".")
            if device == "xpu":
                # XPU uses the patch version in the release branch name
                check_call(
                    ["git", "checkout", f"release/{ver}.{rev}.{patch}"],
                    cwd=triton_basedir,
                )
            else:
                check_call(
                    ["git", "checkout", f"release/{ver}.{rev}.x"], cwd=triton_basedir
                )
        else:
            check_call(["git", "fetch", "origin", commit_hash], cwd=triton_basedir)
            check_call(["git", "checkout", commit_hash], cwd=triton_basedir)

        # change built wheel name and version
        env["TRITON_WHEEL_NAME"] = triton_pkg_name
        env["TRITON_EXT_ENABLED"] = "ON"
        if with_clang_ldd:
            env["TRITON_BUILD_WITH_CLANG_LLD"] = "1"

        patch_init_py(
            triton_pythondir / "triton" / "__init__.py",
            version=f"{version}",
            expected_version=read_triton_version(device),
        )

        if device == "rocm":
            check_call(
                [f"{SCRIPT_DIR}/amd/package_triton_wheel.sh"],
                cwd=triton_basedir,
                shell=True,
            )
            print("ROCm libraries setup for triton installation...")

        # old triton versions have setup.py in the python/ dir,
        # new versions have it in the root dir.
        triton_setupdir = (
            triton_basedir
            if (triton_basedir / "setup.py").exists()
            else triton_pythondir
        )

        check_call(
            [sys.executable, "setup.py", "bdist_wheel"], cwd=triton_setupdir, env=env
        )

        whl_path = next(iter((triton_setupdir / "dist").glob("*.whl")))
        shutil.copy(whl_path, Path.cwd())

        if device == "rocm":
            check_call(
                [f"{SCRIPT_DIR}/amd/patch_triton_wheel.sh", Path.cwd()],
                cwd=triton_basedir,
            )

        return Path.cwd() / whl_path.name