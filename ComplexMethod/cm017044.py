def make_pr(
    *,
    language: Annotated[str | None, typer.Option(envvar="LANGUAGE")] = None,
    command: Annotated[str | None, typer.Option(envvar="COMMAND")] = None,
    github_token: Annotated[str, typer.Option(envvar="GITHUB_TOKEN")],
    github_repository: Annotated[str, typer.Option(envvar="GITHUB_REPOSITORY")],
    commit_in_place: Annotated[
        bool, typer.Option(envvar="COMMIT_IN_PLACE", show_default=True)
    ] = False,
) -> None:
    print("Setting up GitHub Actions git user")
    repo = git.Repo(Path(__file__).absolute().parent.parent)
    if not repo.is_dirty(untracked_files=True):
        print("Repository is clean, no changes to commit")
        return
    subprocess.run(["git", "config", "user.name", "github-actions[bot]"], check=True)
    subprocess.run(
        ["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"],
        check=True,
    )
    current_branch = repo.active_branch.name
    if current_branch == "master" and commit_in_place:
        print("Can't commit directly to master")
        raise typer.Exit(code=1)

    if not commit_in_place:
        branch_name = "translate"
        if language:
            branch_name += f"-{language}"
        if command:
            branch_name += f"-{command}"
        branch_name += f"-{secrets.token_hex(4)}"
        print(f"Creating a new branch {branch_name}")
        subprocess.run(["git", "checkout", "-b", branch_name], check=True)
    else:
        branch_name = current_branch
        print(f"Committing in place on branch {branch_name}")
    print("Adding updated files")
    git_path = Path("docs")
    subprocess.run(["git", "add", str(git_path)], check=True)
    print("Committing updated file")
    message = "🌐 Update translations"
    if language:
        message += f" for {language}"
    if command:
        message += f" ({command})"
    subprocess.run(["git", "commit", "-m", message], check=True)
    print("Pushing branch")
    subprocess.run(["git", "push", "origin", branch_name], check=True)
    if not commit_in_place:
        print("Creating PR")
        g = Github(github_token)
        gh_repo = g.get_repo(github_repository)
        body = (
            message
            + "\n\nThis PR was created automatically using LLMs."
            + f"\n\nIt uses the prompt file https://github.com/fastapi/fastapi/blob/master/docs/{language}/llm-prompt.md."
            + "\n\nIn most cases, it's better to make PRs updating that file so that the LLM can do a better job generating the translations than suggesting changes in this PR."
        )
        pr = gh_repo.create_pull(
            title=message, body=body, base="master", head=branch_name
        )
        print(f"Created PR: {pr.number}")
    print("Finished")