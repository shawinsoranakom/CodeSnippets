def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = Settings()
    logging.info(f"Using config: {settings.model_dump_json()}")
    rate_limiter.speed_multiplier = settings.speed_multiplier
    g = Github(settings.github_token.get_secret_value())
    repo = g.get_repo(settings.github_repository)

    discussion_nodes = get_discussion_nodes(settings=settings)
    experts_results = get_discussions_experts(discussion_nodes=discussion_nodes)

    authors = experts_results.authors
    maintainers_logins = {"tiangolo"}
    maintainers = []
    for login in maintainers_logins:
        user = authors[login]
        maintainers.append(
            {
                "login": login,
                "answers": experts_results.commenters[login],
                "avatarUrl": user.avatarUrl,
                "url": user.url,
            }
        )

    experts = get_users_to_write(
        counter=experts_results.commenters,
        authors=authors,
    )
    last_month_experts = get_users_to_write(
        counter=experts_results.last_month_commenters,
        authors=authors,
    )
    three_months_experts = get_users_to_write(
        counter=experts_results.three_months_commenters,
        authors=authors,
    )
    six_months_experts = get_users_to_write(
        counter=experts_results.six_months_commenters,
        authors=authors,
    )
    one_year_experts = get_users_to_write(
        counter=experts_results.one_year_commenters,
        authors=authors,
    )

    people = {
        "maintainers": maintainers,
        "experts": experts,
        "last_month_experts": last_month_experts,
        "three_months_experts": three_months_experts,
        "six_months_experts": six_months_experts,
        "one_year_experts": one_year_experts,
    }

    # For local development
    # people_path = Path("../docs/en/data/people.yml")
    people_path = Path("./docs/en/data/people.yml")

    updated = update_content(content_path=people_path, new_content=people)

    if not updated:
        logging.info("The data hasn't changed, finishing.")
        return

    logging.info("Setting up GitHub Actions git user")
    subprocess.run(["git", "config", "user.name", "github-actions[bot]"], check=True)
    subprocess.run(
        ["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"],
        check=True,
    )
    branch_name = f"fastapi-people-experts-{secrets.token_hex(4)}"
    logging.info(f"Creating a new branch {branch_name}")
    subprocess.run(["git", "checkout", "-b", branch_name], check=True)
    logging.info("Adding updated file")
    subprocess.run(["git", "add", str(people_path)], check=True)
    logging.info("Committing updated file")
    message = "👥 Update FastAPI People - Experts"
    subprocess.run(["git", "commit", "-m", message], check=True)
    logging.info("Pushing branch")
    subprocess.run(["git", "push", "origin", branch_name], check=True)
    logging.info("Creating PR")
    pr = repo.create_pull(title=message, body=message, base="master", head=branch_name)
    logging.info(f"Created PR: {pr.number}")
    logging.info("Finished")