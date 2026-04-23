def check_version(package: str) -> None:
    release_version = os.getenv("RELEASE_VERSION")
    # if release_version is specified, use it to validate the packages
    if release_version:
        release_matrix = read_release_matrix()
        stable_version = release_matrix["torch"]
    else:
        stable_version = os.getenv("MATRIX_STABLE_VERSION")

    # only makes sense to check nightly package where dates are known
    if channel == "nightly":
        check_nightly_binaries_date(package)
    elif stable_version is not None:
        if not torch.__version__.startswith(stable_version):
            raise RuntimeError(
                f"Torch version mismatch, expected {stable_version} for channel {channel}. But its {torch.__version__}"
            )

        if release_version and package in ["all", "torch_torchvision"]:
            for module in get_modules_for_package(package):
                imported_module = importlib.import_module(module["name"])
                module_version = imported_module.__version__
                if not module_version.startswith(release_matrix[module["name"]]):
                    raise RuntimeError(
                        f"{module['name']} version mismatch, expected: \
                            {release_matrix[module['name']]} for channel {channel}. But its {module_version}"
                    )
                else:
                    print(
                        f"{module['name']} version actual: {module_version} expected: \
                        {release_matrix[module['name']]} for channel {channel}."
                    )

    else:
        print(f"Skip version check for channel {channel} as stable version is None")