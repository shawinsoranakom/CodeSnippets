def print_relevant_docs(template: str, info: Info) -> None:
    """Print relevant docs."""
    data = DATA[template]

    print()
    print("**************************")
    print()
    print()
    print(f"{data['title']} code has been generated")
    print()
    if info.files_added:
        print("Added the following files:")
        for file in info.files_added:
            print(f"- {file}")
        print()

    if info.tests_added:
        print("Added the following tests:")
        for file in info.tests_added:
            print(f"- {file}")
        print()

    if info.examples_added:
        print(
            "Because some files already existed, we added the following example files. Please copy the relevant code to the existing files."
        )
        for file in info.examples_added:
            print(f"- {file}")
        print()

    print(
        "The next step is to look at the files and deal with all areas marked as TODO."
    )

    if "extra" in data:
        print()
        print(data["extra"])