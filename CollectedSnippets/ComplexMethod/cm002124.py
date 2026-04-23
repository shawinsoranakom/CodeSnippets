def main():
    script_dir = Path(__file__).parent.absolute()
    with open(script_dir / "codeowners_for_review_action") as f:
        codeowners_lines = f.readlines()

    g = Github(os.environ['GITHUB_TOKEN'])
    repo = g.get_repo("huggingface/transformers")
    with open(os.environ['GITHUB_EVENT_PATH']) as f:
        event = json.load(f)

    # The PR number is available in the event payload
    pr_number = event['pull_request']['number']
    pr = repo.get_pull(pr_number)
    pr_author = pr.user.login
    if pr_author_is_in_hf(pr_author, codeowners_lines):
        print(f"PR author {pr_author} is in codeowners, skipping review request.")
        return

    existing_reviews = list(pr.get_reviews())
    if existing_reviews:
        print(f"Already has reviews: {[r.user.login for r in existing_reviews]}")
        return

    users_requested, teams_requested = pr.get_review_requests()
    users_requested = list(users_requested)
    if users_requested:
        print(f"Reviewers already requested: {users_requested}")
        return

    locs_per_owner = Counter()
    for file in pr.get_files():
        owners = get_file_owners(file.filename, codeowners_lines)
        for owner in owners:
            locs_per_owner[owner] += file.changes

    # Assign the top 2 based on locs changed as reviewers, but skip the owner if present
    locs_per_owner.pop(pr_author, None)
    top_owners = locs_per_owner.most_common(2)
    print("Top owners", top_owners)
    top_owners = [owner[0] for owner in top_owners]
    try:
        pr.create_review_request(top_owners)
    except github.GithubException as e:
        print(f"Failed to request review for {top_owners}: {e}")