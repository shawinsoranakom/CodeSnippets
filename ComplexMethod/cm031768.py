def process_changed_files(changed_files: Set[Path]) -> Outputs:
    run_tests = False
    run_ci_fuzz = False
    run_ci_fuzz_stdlib = False
    run_docs = False
    run_windows_tests = False
    run_windows_msi = False

    platforms_changed = set()
    has_platform_specific_change = True

    for file in changed_files:
        # Documentation files
        doc_or_misc = file.parts[0] in {"Doc", "Misc"}
        doc_file = file.suffix in SUFFIXES_DOCUMENTATION or doc_or_misc

        if file.parent == GITHUB_WORKFLOWS_PATH:
            if file.name in ("build.yml", "reusable-cifuzz.yml"):
                run_tests = run_ci_fuzz = run_ci_fuzz_stdlib = run_windows_tests = True
                has_platform_specific_change = False
                continue
            if file.name in ("reusable-docs.yml", "reusable-check-html-ids.yml"):
                run_docs = True
                continue
            if file.name == "reusable-windows.yml":
                run_tests = True
                run_windows_tests = True
                continue
            if file.name == "reusable-windows-msi.yml":
                run_windows_msi = True
                continue
            if file.name == "reusable-macos.yml":
                run_tests = True
                platforms_changed.add("macos")
                continue
            if file.name == "reusable-emscripten.yml":
                run_tests = True
                platforms_changed.add("emscripten")
                continue
            if file.name == "reusable-wasi.yml":
                run_tests = True
                platforms_changed.add("wasi")
                continue

        if not doc_file and file not in RUN_TESTS_IGNORE:
            run_tests = True

            platform = get_file_platform(file)
            if platform is not None:
                platforms_changed.add(platform)
            else:
                has_platform_specific_change = False
                if file not in UNIX_BUILD_SYSTEM_FILE_NAMES:
                    run_windows_tests = True

        # The fuzz tests are pretty slow so they are executed only for PRs
        # changing relevant files.
        if file.suffix in SUFFIXES_C_OR_CPP:
            run_ci_fuzz = True
        if file.parts[:2] in {
            ("configure",),
            ("Modules", "_xxtestfuzz"),
        }:
            run_ci_fuzz = True
        if not run_ci_fuzz_stdlib and is_fuzzable_library_file(file):
            run_ci_fuzz_stdlib = True

        # Check for changed documentation-related files
        if doc_file:
            run_docs = True

        # Check for changed MSI installer-related files
        if file.parts[:2] == ("Tools", "msi"):
            run_windows_msi = True

    # Check which platform specific tests to run
    if run_tests:
        if not has_platform_specific_change or not platforms_changed:
            run_android = True
            run_emscripten = True
            run_ios = True
            run_macos = True
            run_ubuntu = True
            run_wasi = True
        else:
            run_android = "android" in platforms_changed
            run_emscripten = "emscripten" in platforms_changed
            run_ios = "ios" in platforms_changed
            run_macos = "macos" in platforms_changed
            run_ubuntu = False
            run_wasi = "wasi" in platforms_changed
    else:
        run_android = False
        run_emscripten = False
        run_ios = False
        run_macos = False
        run_ubuntu = False
        run_wasi = False

    return Outputs(
        run_android=run_android,
        run_ci_fuzz=run_ci_fuzz,
        run_ci_fuzz_stdlib=run_ci_fuzz_stdlib,
        run_docs=run_docs,
        run_emscripten=run_emscripten,
        run_ios=run_ios,
        run_macos=run_macos,
        run_tests=run_tests,
        run_ubuntu=run_ubuntu,
        run_wasi=run_wasi,
        run_windows_msi=run_windows_msi,
        run_windows_tests=run_windows_tests,
    )