def create_xcframework(platform: str) -> str:
    """Build an XCframework from the component parts for the platform.

    :return: The version number of the Python version that was packaged.
    """
    package_path = CROSS_BUILD_DIR / platform
    try:
        package_path.mkdir()
    except FileExistsError:
        raise RuntimeError(
            f"{platform} XCframework already exists; do you need to run "
            "with --clean?"
        ) from None

    frameworks = []
    # Merge Frameworks for each component SDK. If there's only one architecture
    # for the SDK, we can use the compiled Python.framework as-is. However, if
    # there's more than architecture, we need to merge the individual built
    # frameworks into a merged "fat" framework.
    for slice_name, slice_parts in HOSTS[platform].items():
        # Some parts are the same across all slices, so we use can any of the
        # host frameworks as the source for the merged version. Use the first
        # one on the list, as it's as representative as any other.
        first_host_triple, first_multiarch = next(iter(slice_parts.items()))
        first_framework = (
            framework_path(first_host_triple, first_multiarch)
            / "Python.framework"
        )

        if len(slice_parts) == 1:
            # The first framework is the only framework, so copy it.
            print(f"Copying framework for {slice_name}...")
            frameworks.append(first_framework)
        else:
            print(f"Merging framework for {slice_name}...")
            slice_path = CROSS_BUILD_DIR / slice_name
            slice_framework = slice_path / "Python.framework"
            slice_framework.mkdir(exist_ok=True, parents=True)

            # Copy the Info.plist
            shutil.copy(
                first_framework / "Info.plist",
                slice_framework / "Info.plist",
            )

            # Copy the headers
            shutil.copytree(
                first_framework / "Headers",
                slice_framework / "Headers",
            )

            # Create the "fat" library binary for the slice
            run(
                ["lipo", "-create", "-output", slice_framework / "Python"]
                + [
                    (
                        framework_path(host_triple, multiarch)
                        / "Python.framework/Python"
                    )
                    for host_triple, multiarch in slice_parts.items()
                ]
            )

            # Add this merged slice to the list to be added to the XCframework
            frameworks.append(slice_framework)

    print()
    print("Build XCframework...")
    cmd = [
        "xcodebuild",
        "-create-xcframework",
        "-output",
        package_path / "Python.xcframework",
    ]
    for framework in frameworks:
        cmd.extend(["-framework", framework])

    run(cmd)

    # Extract the package version from the merged framework
    version = package_version(package_path / "Python.xcframework")
    version_tag = ".".join(version.split(".")[:2])

    # On non-macOS platforms, each framework in XCframework only contains the
    # headers, libPython, plus an Info.plist. Other resources like the standard
    # library and binary shims aren't allowed to live in framework; they need
    # to be copied in separately.
    print()
    print("Copy additional resources...")
    has_common_stdlib = False
    for slice_name, slice_parts in HOSTS[platform].items():
        # Some parts are the same across all slices, so we can any of the
        # host frameworks as the source for the merged version.
        first_host_triple, first_multiarch = next(iter(slice_parts.items()))
        first_path = framework_path(first_host_triple, first_multiarch)
        first_framework = first_path / "Python.framework"

        slice_path = package_path / f"Python.xcframework/{slice_name}"
        slice_framework = slice_path / "Python.framework"

        # Copy the binary helpers
        print(f" - {slice_name} binaries")
        shutil.copytree(first_path / "bin", slice_path / "bin")

        # Copy the include path (a symlink to the framework headers)
        print(f" - {slice_name} include files")
        shutil.copytree(
            first_path / "include",
            slice_path / "include",
            symlinks=True,
        )

        # Copy in the cross-architecture pyconfig.h
        shutil.copy(
            PYTHON_DIR / f"Platforms/Apple/{platform}/Resources/pyconfig.h",
            slice_framework / "Headers/pyconfig.h",
        )

        print(f" - {slice_name} shared library")
        # Create a simlink for the fat library
        shared_lib = slice_path / f"lib/libpython{version_tag}.dylib"
        shared_lib.parent.mkdir()
        shared_lib.symlink_to("../Python.framework/Python")

        print(f" - {slice_name} architecture-specific files")
        for host_triple, multiarch in slice_parts.items():
            print(f"   - {multiarch} standard library")
            arch, _ = multiarch.split("-", 1)

            if not has_common_stdlib:
                print("     - using this architecture as the common stdlib")
                shutil.copytree(
                    framework_path(host_triple, multiarch) / "lib",
                    package_path / "Python.xcframework/lib",
                    ignore=lib_platform_files,
                    symlinks=True,
                )
                has_common_stdlib = True

            shutil.copytree(
                framework_path(host_triple, multiarch) / "lib",
                slice_path / f"lib-{arch}",
                ignore=lib_non_platform_files,
                symlinks=True,
            )

            # Copy the host's pyconfig.h to an architecture-specific name.
            arch = multiarch.split("-")[0]
            host_path = (
                CROSS_BUILD_DIR
                / host_triple
                / "Platforms/Apple/iOS/Frameworks"
                / multiarch
            )
            host_framework = host_path / "Python.framework"
            shutil.copy(
                host_framework / "Headers/pyconfig.h",
                slice_framework / f"Headers/pyconfig-{arch}.h",
            )

            # Apple identifies certain libraries as "security risks"; if you
            # statically link those libraries into a Framework, you become
            # responsible for providing a privacy manifest for that framework.
            xcprivacy_file = {
                "OpenSSL": subdir(host_triple)
                / "prefix/share/OpenSSL.xcprivacy"
            }
            print(f"   - {multiarch} xcprivacy files")
            for module, lib in [
                ("_hashlib", "OpenSSL"),
                ("_ssl", "OpenSSL"),
            ]:
                shutil.copy(
                    xcprivacy_file[lib],
                    slice_path
                    / f"lib-{arch}/python{version_tag}"
                    / f"lib-dynload/{module}.xcprivacy",
                )

    print(" - build tools")
    shutil.copytree(
        PYTHON_DIR / "Platforms/Apple/testbed/Python.xcframework/build",
        package_path / "Python.xcframework/build",
    )

    return version