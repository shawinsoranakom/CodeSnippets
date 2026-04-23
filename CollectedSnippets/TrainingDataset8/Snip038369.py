def _maybe_print_old_git_warning(main_script_path: str) -> None:
    """If our script is running in a Git repo, and we're running a very old
    Git version, print a warning that Git integration will be unavailable.
    """
    repo = GitRepo(main_script_path)
    if (
        not repo.is_valid()
        and repo.git_version is not None
        and repo.git_version < MIN_GIT_VERSION
    ):
        git_version_string = ".".join(str(val) for val in repo.git_version)
        min_version_string = ".".join(str(val) for val in MIN_GIT_VERSION)
        click.secho("")
        click.secho("  Git integration is disabled.", fg="yellow", bold=True)
        click.secho("")
        click.secho(
            f"  Streamlit requires Git {min_version_string} or later, "
            f"but you have {git_version_string}.",
            fg="yellow",
        )
        click.secho(
            "  Git is used by Streamlit Cloud (https://streamlit.io/cloud).",
            fg="yellow",
        )
        click.secho("  To enable this feature, please update Git.", fg="yellow")