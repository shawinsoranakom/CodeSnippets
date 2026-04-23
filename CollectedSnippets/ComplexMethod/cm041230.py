def package_for_lang(scenario: str, runtime: str, root_folder: Path) -> str:
    """
    :param scenario: which scenario to run
    :param runtime: which runtime to build
    :param root_folder: The root folder for the scenarios
    :return: path to built zip file
    """
    runtime_folder = PACKAGE_FOR_RUNTIME[runtime]

    common_dir = root_folder / "functions" / "common"
    scenario_dir = common_dir / scenario
    runtime_dir_candidate = scenario_dir / runtime
    generic_runtime_dir_candidate = scenario_dir / runtime_folder

    # if a more specific folder exists, use that one
    # otherwise: try to fall back to generic runtime (e.g. python for python3.12)
    if runtime_dir_candidate.exists() and runtime_dir_candidate.is_dir():
        runtime_dir = runtime_dir_candidate
    else:
        runtime_dir = generic_runtime_dir_candidate

    build_dir = runtime_dir / "build"
    package_path = runtime_dir / "handler.zip"

    # caching step
    # TODO: add invalidation (e.g. via storing a hash besides this of all files in src)
    if os.path.exists(package_path) and os.path.isfile(package_path):
        return package_path

    # packaging
    # Use the default Lambda architecture x86_64 unless the ignore architecture flag is configured.
    # This enables local testing of both architectures on multi-architecture platforms such as Apple Silicon machines.
    architecture = "x86_64"
    if config.LAMBDA_IGNORE_ARCHITECTURE:
        architecture = "arm64" if get_arch() == Arch.arm64 else "x86_64"
    build_cmd = ["make", "build", f"ARCHITECTURE={architecture}"]
    LOG.debug(
        "Building Lambda function for scenario %s and runtime %s using %s.",
        scenario,
        runtime,
        " ".join(build_cmd),
    )
    result = subprocess.run(build_cmd, cwd=runtime_dir)
    if result.returncode != 0:
        raise Exception(
            f"Failed to build multiruntime {scenario=} for {runtime=} with error code: {result.returncode}"
        )

    # check again if the zip file is now present
    if os.path.exists(package_path) and os.path.isfile(package_path):
        return package_path

    # check something is in build now
    target_empty = len(os.listdir(build_dir)) <= 0
    if target_empty:
        raise Exception(f"Failed to build multiruntime {scenario=} for {runtime=} ")

    with zipfile.ZipFile(package_path, "w", strict_timestamps=True) as zf:
        for root, dirs, files in os.walk(build_dir):
            rel_dir = os.path.relpath(root, build_dir)
            for f in files:
                zf.write(os.path.join(root, f), arcname=os.path.join(rel_dir, f))

    # make sure package file has been generated
    assert package_path.exists() and package_path.is_file()
    return package_path