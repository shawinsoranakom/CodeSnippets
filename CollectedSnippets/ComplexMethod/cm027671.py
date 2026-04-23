async def main():
    """Run the main loop."""
    # Ensure we are in the homeassistant root
    os.chdir(Path(__file__).parent.parent)

    files = await git()
    if not files:
        print(
            "No changed files found. Please ensure you have added your "
            "changes with git add & git commit"
        )
        return

    pyfiles = [file for file in files if file.endswith(".py")]

    print("=============================")
    printc("bold", "CHANGED FILES:\n", "\n ".join(pyfiles))
    print("=============================")

    skip_lint = len(sys.argv) > 1 and sys.argv[1] == "--skiplint"
    if skip_lint:
        printc(FAIL, "LINT DISABLED")
    elif not await lint(pyfiles):
        printc(FAIL, "Please fix your lint issues before continuing")
        return

    test_files = set()
    gen_req = False
    for fname in pyfiles:
        if fname.startswith("homeassistant/components/"):
            gen_req = True  # requirements script for components
        # Find test files...
        if fname.startswith("tests/"):
            if "/test_" in fname and Path(fname).is_file():
                # All test helpers should be excluded
                test_files.add(fname)
        else:
            parts = fname.split("/")
            parts[0] = "tests"
            if parts[-1] == "__init__.py":
                parts[-1] = "test_init.py"
            elif parts[-1] == "__main__.py":
                parts[-1] = "test_main.py"
            else:
                parts[-1] = f"test_{parts[-1]}"
            fname = "/".join(parts)
            if Path(fname).is_file():
                test_files.add(fname)

    if gen_req:
        print("=============================")
        if validate_requirements_ok():
            printc(PASS, "script/gen_requirements.py passed")
        else:
            printc(FAIL, "Please run script/gen_requirements.py")
            return

    print("=============================")
    if not test_files:
        print("No test files identified")
        return

    code, _ = await async_exec(
        "python3",
        "-b",
        "-m",
        "pytest",
        "-vv",
        "--force-sugar",
        "--",
        *test_files,
        display=True,
    )
    print("=============================")

    if code == 0:
        printc(PASS, "Yay! This will most likely pass CI")
    else:
        printc(FAIL, "Tests not passing")

    if skip_lint:
        printc(FAIL, "LINT DISABLED")