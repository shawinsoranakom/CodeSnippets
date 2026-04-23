def main(validate: bool, ci: bool) -> int:
    """Run the script."""
    if not Path("requirements_all.txt").is_file():
        print("Run this from HA root dir")
        return 1

    data = gather_modules()

    if data is None:
        return 1

    reqs_file = requirements_output()
    reqs_all_file = requirements_all_output(data)
    reqs_all_action_files = {
        action: requirements_all_action_output(data, action)
        for action in OVERRIDDEN_REQUIREMENTS_ACTIONS
    }
    reqs_test_all_file = requirements_test_all_output(data)
    # Always calling requirements_pre_commit_output is intentional to ensure
    # the code is called by the pre-commit hooks.
    reqs_pre_commit_file = requirements_pre_commit_output()
    constraints = gather_constraints()

    files = [
        ("requirements.txt", reqs_file),
        ("requirements_all.txt", reqs_all_file),
        ("requirements_test_pre_commit.txt", reqs_pre_commit_file),
        ("requirements_test_all.txt", reqs_test_all_file),
        ("homeassistant/package_constraints.txt", constraints),
    ]
    if ci:
        files.extend(
            (f"requirements_all_{action}.txt", reqs_all_file)
            for action, reqs_all_file in reqs_all_action_files.items()
        )

    if validate:
        errors = []

        for filename, content in files:
            diff = diff_file(filename, content)
            if diff:
                errors.append("".join(diff))

        if errors:
            print("ERROR - FOUND THE FOLLOWING DIFFERENCES")
            print()
            print()
            print("\n\n".join(errors))
            print()
            print("Please run python3 -m script.gen_requirements_all")
            return 1

        return 0

    for filename, content in files:
        Path(filename).write_text(content)

    return 0