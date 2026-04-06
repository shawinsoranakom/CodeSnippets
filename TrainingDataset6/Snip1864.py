def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = Settings()
    logging.info(f"Using config: {settings.model_dump_json()}")
    g = Github(settings.github_token.get_secret_value())
    repo = g.get_repo(settings.github_repository)

    pr_nodes = get_pr_nodes(settings=settings)
    contributors_results = get_contributors(pr_nodes=pr_nodes)
    authors = contributors_results.authors

    top_contributors = get_users_to_write(
        counter=contributors_results.contributors,
        authors=authors,
    )

    top_translators = get_users_to_write(
        counter=contributors_results.translators,
        authors=authors,
    )
    top_translations_reviewers = get_users_to_write(
        counter=contributors_results.translation_reviewers,
        authors=authors,
    )

    # For local development
    # contributors_path = Path("../docs/en/data/contributors.yml")
    contributors_path = Path("./docs/en/data/contributors.yml")
    # translators_path = Path("../docs/en/data/translators.yml")
    translators_path = Path("./docs/en/data/translators.yml")
    # translation_reviewers_path = Path("../docs/en/data/translation_reviewers.yml")
    translation_reviewers_path = Path("./docs/en/data/translation_reviewers.yml")

    updated = [
        update_content(content_path=contributors_path, new_content=top_contributors),
        update_content(content_path=translators_path, new_content=top_translators),
        update_content(
            content_path=translation_reviewers_path,
            new_content=top_translations_reviewers,
        ),
    ]

    if not any(updated):
        logging.info("The data hasn't changed, finishing.")
        return

    logging.info("Setting up GitHub Actions git user")
    subprocess.run(["git", "config", "user.name", "github-actions[bot]"], check=True)
    subprocess.run(
        ["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"],
        check=True,
    )
    branch_name = f"fastapi-people-contributors-{secrets.token_hex(4)}"
    logging.info(f"Creating a new branch {branch_name}")
    subprocess.run(["git", "checkout", "-b", branch_name], check=True)
    logging.info("Adding updated file")
    subprocess.run(
        [
            "git",
            "add",
            str(contributors_path),
            str(translators_path),
            str(translation_reviewers_path),
        ],
        check=True,
    )
    logging.info("Committing updated file")
    message = "👥 Update FastAPI People - Contributors and Translators"
    subprocess.run(["git", "commit", "-m", message], check=True)
    logging.info("Pushing branch")
    subprocess.run(["git", "push", "origin", branch_name], check=True)
    logging.info("Creating PR")
    pr = repo.create_pull(title=message, body=message, base="master", head=branch_name)
    logging.info(f"Created PR: {pr.number}")
    logging.info("Finished")