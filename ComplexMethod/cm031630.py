def clone_testbed(
    source: Path,
    target: Path,
    framework: Path,
    platform: str,
    apps: list[Path],
) -> None:
    if target.exists():
        print(f"{target} already exists; aborting without creating project.")
        sys.exit(10)

    if framework is None:
        if not (
            source / "Python.xcframework" / TEST_SLICES[platform] / "bin"
        ).is_dir():
            print(
                f"The testbed being cloned ({source}) does not contain "
                "a framework with slices. Re-run with --framework"
            )
            sys.exit(11)
    else:
        if not framework.is_dir():
            print(f"{framework} does not exist.")
            sys.exit(12)
        elif not (
            framework.suffix == ".xcframework"
            or (framework / "Python.framework").is_dir()
        ):
            print(
                f"{framework} is not an XCframework, "
                f"or a simulator slice of a framework build."
            )
            sys.exit(13)

    print("Cloning testbed project:")
    print(f"  Cloning {source}...", end="")
    # Only copy the files for the platform being cloned plus the files common
    # to all platforms. The XCframework will be copied later, if needed.
    target.mkdir(parents=True)

    for name in [
        "__main__.py",
        "TestbedTests",
        "Testbed.lldbinit",
        f"{platform}Testbed",
        f"{platform}Testbed.xcodeproj",
        f"{platform}Testbed.xctestplan",
    ]:
        copy(source / name, target / name)

    print(" done")

    orig_xc_framework_path = source / "Python.xcframework"
    xc_framework_path = target / "Python.xcframework"
    test_framework_path = xc_framework_path / TEST_SLICES[platform]
    if framework is not None:
        if framework.suffix == ".xcframework":
            print("  Installing XCFramework...", end="")
            xc_framework_path.symlink_to(
                framework.relative_to(xc_framework_path.parent, walk_up=True)
            )
            print(" done")
        else:
            print("  Installing simulator framework...", end="")
            # We're only installing a slice of a framework; we need
            # to do a full tree copy to make sure we don't damage
            # symlinked content.
            shutil.copytree(orig_xc_framework_path, xc_framework_path)
            if test_framework_path.is_dir():
                shutil.rmtree(test_framework_path)
            else:
                test_framework_path.unlink(missing_ok=True)
            test_framework_path.symlink_to(
                framework.relative_to(test_framework_path.parent, walk_up=True)
            )
            print(" done")
    else:
        copy(orig_xc_framework_path, xc_framework_path)

        if (
            xc_framework_path.is_symlink()
            and not xc_framework_path.readlink().is_absolute()
        ):
            # XCFramework is a relative symlink. Rewrite the symlink relative
            # to the new location.
            print("  Rewriting symlink to XCframework...", end="")
            resolved_xc_framework_path = (
                source / xc_framework_path.readlink()
            ).resolve()
            xc_framework_path.unlink()
            xc_framework_path.symlink_to(
                resolved_xc_framework_path.relative_to(
                    xc_framework_path.parent, walk_up=True
                )
            )
            print(" done")
        elif (
            test_framework_path.is_symlink()
            and not test_framework_path.readlink().is_absolute()
        ):
            print("  Rewriting symlink to simulator framework...", end="")
            # Simulator framework is a relative symlink. Rewrite the symlink
            # relative to the new location.
            orig_test_framework_path = (
                source / "Python.XCframework" / test_framework_path.readlink()
            ).resolve()
            test_framework_path.unlink()
            test_framework_path.symlink_to(
                orig_test_framework_path.relative_to(
                    test_framework_path.parent, walk_up=True
                )
            )
            print(" done")
        else:
            print("  Using pre-existing Python framework.")

    for app_src in apps:
        print(f"  Installing app {app_src.name!r}...", end="")
        app_target = target / f"Testbed/app/{app_src.name}"
        if app_target.is_dir():
            shutil.rmtree(app_target)
        shutil.copytree(app_src, app_target)
        print(" done")

    print(f"Successfully cloned testbed: {target.resolve()}")