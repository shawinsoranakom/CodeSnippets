def compute_changes() -> None:
    target_ref, head_ref = git_refs()
    if os.environ.get("GITHUB_EVENT_NAME", "") == "pull_request":
        # Getting changed files only makes sense on a pull request
        files = get_changed_files(target_ref, head_ref)
        outputs = process_changed_files(files)
    else:
        # Otherwise, just run the tests
        outputs = Outputs(
            run_android=True,
            run_emscripten=True,
            run_ios=True,
            run_macos=True,
            run_tests=True,
            run_ubuntu=True,
            run_wasi=True,
            run_windows_tests=True,
        )
    target_branch = target_ref.removeprefix("origin/")
    outputs = process_target_branch(outputs, target_branch)

    if outputs.run_tests:
        print("Run tests")
    if outputs.run_windows_tests:
        print("Run Windows tests")

    if outputs.run_ci_fuzz:
        print("Run CIFuzz tests")
    else:
        print("Branch too old for CIFuzz tests; or no C files were changed")

    if outputs.run_ci_fuzz_stdlib:
        print("Run CIFuzz tests for stdlib")
    else:
        print("Branch too old for CIFuzz tests; or no stdlib files were changed")

    if outputs.run_docs:
        print("Build documentation")

    if outputs.run_windows_msi:
        print("Build Windows MSI")

    print(outputs)

    write_github_output(outputs)