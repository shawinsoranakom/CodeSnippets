def main():
    gaia_validation_files = os.path.join(REPO_DIR, "2023", "validation")
    gaia_test_files = os.path.join(REPO_DIR, "2023", "test")

    if not os.path.isdir(gaia_validation_files) or not os.path.isdir(gaia_test_files):
        download_gaia()

    if not os.path.isdir(gaia_validation_files) or not os.path.isdir(gaia_test_files):
        sys.exit(f"Error: '{REPO_DIR}' does not appear to be a copy of the GAIA repository.")

    # Load the GAIA data
    gaia_validation_tasks = [[], [], []]
    with open(os.path.join(gaia_validation_files, "metadata.jsonl")) as fh:
        for line in fh:
            data = json.loads(line)
            gaia_validation_tasks[data["Level"] - 1].append(data)

    gaia_test_tasks = [[], [], []]
    with open(os.path.join(gaia_test_files, "metadata.jsonl")) as fh:
        for line in fh:
            data = json.loads(line)

            # A welcome message -- not a real task
            if data["task_id"] == "0-0-0-0-0":
                continue

            gaia_test_tasks[data["Level"] - 1].append(data)

    # list all directories in the Templates directory
    # and populate a dictionary with the name and path
    templates = {}
    for entry in os.scandir(TEMPLATES_DIR):
        if entry.is_dir():
            templates[re.sub(r"\s", "", entry.name)] = entry.path

    # Add coding directories if needed (these are usually empty and left out of the repo)
    #for template in templates.values():
    #    code_dir_path = os.path.join(template, "coding")
    #    if not os.path.isdir(code_dir_path):
    #        os.mkdir(code_dir_path)

    # Create the various combinations of [models] x [templates]
    for t in templates.items():
        create_jsonl(
            f"gaia_validation_level_1__{t[0]}",
            gaia_validation_tasks[0],
            gaia_validation_files,
            t[1],
        )
        create_jsonl(
            f"gaia_validation_level_2__{t[0]}",
            gaia_validation_tasks[1],
            gaia_validation_files,
            t[1],
        )
        create_jsonl(
            f"gaia_validation_level_3__{t[0]}",
            gaia_validation_tasks[2],
            gaia_validation_files,
            t[1],
        )
        create_jsonl(
            f"gaia_test_level_1__{t[0]}",
            gaia_test_tasks[0],
            gaia_test_files,
            t[1],
        )
        create_jsonl(
            f"gaia_test_level_2__{t[0]}",
            gaia_test_tasks[1],
            gaia_test_files,
            t[1],
        )
        create_jsonl(
            f"gaia_test_level_3__{t[0]}",
            gaia_test_tasks[2],
            gaia_test_files,
            t[1],
        )