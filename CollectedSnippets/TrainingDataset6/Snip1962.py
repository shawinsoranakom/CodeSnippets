def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = Settings()
    logging.info(f"Using config: {settings.model_dump_json()}")
    g = Github(settings.pr_token.get_secret_value())
    repo = g.get_repo(settings.github_repository)

    tiers = get_individual_sponsors(settings=settings)
    keys = list(tiers.keys())
    keys.sort(reverse=True)
    sponsors = []
    for key in keys:
        sponsor_group = []
        for login, sponsor in tiers[key].items():
            sponsor_group.append(
                {"login": login, "avatarUrl": sponsor.avatarUrl, "url": sponsor.url}
            )
        sponsors.append(sponsor_group)
    github_sponsors = {
        "sponsors": sponsors,
    }

    # For local development
    # github_sponsors_path = Path("../docs/en/data/github_sponsors.yml")
    github_sponsors_path = Path("./docs/en/data/github_sponsors.yml")
    updated = update_content(
        content_path=github_sponsors_path, new_content=github_sponsors
    )

    if not updated:
        logging.info("The data hasn't changed, finishing.")
        return

    logging.info("Setting up GitHub Actions git user")
    subprocess.run(["git", "config", "user.name", "github-actions[bot]"], check=True)
    subprocess.run(
        ["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"],
        check=True,
    )
    branch_name = f"fastapi-people-sponsors-{secrets.token_hex(4)}"
    logging.info(f"Creating a new branch {branch_name}")
    subprocess.run(["git", "checkout", "-b", branch_name], check=True)
    logging.info("Adding updated file")
    subprocess.run(
        [
            "git",
            "add",
            str(github_sponsors_path),
        ],
        check=True,
    )
    logging.info("Committing updated file")
    message = "👥 Update FastAPI People - Sponsors"
    subprocess.run(["git", "commit", "-m", message], check=True)
    logging.info("Pushing branch")
    subprocess.run(["git", "push", "origin", branch_name], check=True)
    logging.info("Creating PR")
    pr = repo.create_pull(title=message, body=message, base="master", head=branch_name)
    logging.info(f"Created PR: {pr.number}")
    logging.info("Finished")