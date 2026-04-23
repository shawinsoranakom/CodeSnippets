def determine_wheel_url() -> tuple[str, str | None]:
        """
        Try to determine the precompiled wheel URL or path to use.
        The order of preference is:
        1. user-specified wheel location (can be either local or remote, via
           VLLM_PRECOMPILED_WHEEL_LOCATION)
        2. user-specified variant (VLLM_PRECOMPILED_WHEEL_VARIANT) from nightly repo
           or auto-detected CUDA variant based on system (torch, nvidia-smi)
        3. the default variant from nightly repo

        If downloading from the nightly repo, the commit can be specified via
        VLLM_PRECOMPILED_WHEEL_COMMIT; otherwise, the head commit in the main branch
        is used.
        """
        wheel_location = os.getenv("VLLM_PRECOMPILED_WHEEL_LOCATION", None)
        if wheel_location is not None:
            print(f"Using user-specified precompiled wheel location: {wheel_location}")
            return wheel_location, None
        else:
            # ROCm: use local wheel or AMD's PyPI index
            # TODO: When we have ROCm nightly wheels, we can update this logic.
            if precompiled_wheel_utils.is_rocm_system():
                return precompiled_wheel_utils.determine_wheel_url_rocm()

            import platform

            arch = platform.machine()
            # try to fetch the wheel metadata from the nightly wheel repo,
            # detecting CUDA variant from system if not specified
            variant = os.getenv("VLLM_PRECOMPILED_WHEEL_VARIANT", None)
            if variant is None:
                variant = precompiled_wheel_utils.detect_system_cuda_variant()
            commit = os.getenv("VLLM_PRECOMPILED_WHEEL_COMMIT", "").lower()
            if not commit or len(commit) != 40:
                print(
                    f"VLLM_PRECOMPILED_WHEEL_COMMIT not valid: {commit}"
                    ", trying to fetch base commit in main branch"
                )
                commit = precompiled_wheel_utils.get_base_commit_in_main_branch()
            print(f"Using precompiled wheel commit {commit} with variant {variant}")
            try_default = False
            wheels, repo_url, download_filename = None, None, None
            try:
                wheels, repo_url = precompiled_wheel_utils.fetch_metadata_for_variant(
                    commit, variant
                )
            except Exception as e:
                logger.warning(
                    "Failed to fetch precompiled wheel metadata for variant %s: %s",
                    variant,
                    e,
                )
                try_default = True  # try outside handler to keep the stacktrace simple
            if try_default:
                print("Trying the default variant from remote")
                wheels, repo_url = precompiled_wheel_utils.fetch_metadata_for_variant(
                    commit, None
                )
                # if this also fails, then we have nothing more to try / cache
            assert wheels is not None and repo_url is not None, (
                "Failed to fetch precompiled wheel metadata"
            )
            # The metadata.json has the following format:
            # see .buildkite/scripts/generate-nightly-index.py for details
            """[{
    "package_name": "vllm",
    "version": "0.11.2.dev278+gdbc3d9991",
    "build_tag": null,
    "python_tag": "cp38",
    "abi_tag": "abi3",
    "platform_tag": "manylinux1_x86_64",
    "variant": null,
    "filename": "vllm-0.11.2.dev278+gdbc3d9991-cp38-abi3-manylinux1_x86_64.whl",
    "path": "../vllm-0.11.2.dev278%2Bgdbc3d9991-cp38-abi3-manylinux1_x86_64.whl"
    },
    ...]"""
            from urllib.parse import urljoin

            for wheel in wheels:
                # TODO: maybe check more compatibility later? (python_tag, abi_tag, etc)
                if wheel.get("package_name") == "vllm" and arch in wheel.get(
                    "platform_tag", ""
                ):
                    print(f"Found precompiled wheel metadata: {wheel}")
                    if "path" not in wheel:
                        raise ValueError(f"Wheel metadata missing path: {wheel}")
                    wheel_url = urljoin(repo_url, wheel["path"])
                    download_filename = wheel.get("filename")
                    print(f"Using precompiled wheel URL: {wheel_url}")
                    break
            else:
                raise ValueError(
                    f"No precompiled vllm wheel found for architecture {arch} "
                    f"from repo {repo_url}. All available wheels: {wheels}"
                )

        return wheel_url, download_filename