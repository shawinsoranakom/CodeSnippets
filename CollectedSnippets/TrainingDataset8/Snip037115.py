def get_container_cwd():

    cwd_path = Path(os.getcwd())
    if not is_relative_to(cwd_path, ROOT_DIR):
        print(
            textwrap.dedent(
                "You must be in your repository directory to run this command.\n"
                "To go to the repository, run command:\n"
                f"    cd {str(ROOT_DIR)}"
            ),
            file=sys.stderr,
        )
        sys.exit(1)
    return str(IN_CONTAINER_HOME / cwd_path.relative_to(ROOT_DIR))