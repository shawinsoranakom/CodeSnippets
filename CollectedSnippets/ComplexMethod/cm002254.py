def get_modified_cards() -> list[str]:
    """Get the list of model names from modified files in docs/source/en/model_doc/"""

    current_branch = subprocess.check_output(["git", "branch", "--show-current"], text=True).strip()
    if current_branch == "main":
        # On main branch, only uncommitted changes detected
        result = subprocess.check_output(["git", "diff", "--name-only", "HEAD"], text=True)
    else:
        fork_point_sha = subprocess.check_output("git merge-base main HEAD".split()).decode("utf-8")
        result = subprocess.check_output(f"git diff --name-only {fork_point_sha}".split()).decode("utf-8")

    model_names = []
    for line in result.strip().split("\n"):
        if line:
            # Check if the file is in the model_doc directory
            if line.startswith("docs/source/en/model_doc/") and line.endswith(".md"):
                file_path = os.path.join(ROOT, line)
                if os.path.exists(file_path):
                    model_name = os.path.splitext(os.path.basename(line))[0]
                    if model_name not in ["auto", "timm_wrapper"]:
                        model_names.append(model_name)

    return model_names