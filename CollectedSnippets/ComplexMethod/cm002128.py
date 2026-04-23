def main():
    g = Github(os.environ["GITHUB_TOKEN"])
    repo = g.get_repo("huggingface/transformers")
    open_issues = repo.get_issues(state="open")

    for i, issue in enumerate(open_issues):
        print(i, issue)
        comments = sorted(issue.get_comments(), key=lambda i: i.created_at, reverse=True)
        last_comment = comments[0] if len(comments) > 0 else None
        if (
            last_comment is not None
            and last_comment.user.login == "github-actions[bot]"
            and (dt.utcnow() - issue.updated_at.replace(tzinfo=None)).days > 7
            and (dt.utcnow() - issue.created_at.replace(tzinfo=None)).days >= 30
            and not any(label.name.lower() in LABELS_TO_EXEMPT for label in issue.get_labels())
        ):
            # print(f"Would close issue {issue.number} since it has been 7 days of inactivity since bot mention.")
            try:
                issue.edit(state="closed")
            except github.GithubException as e:
                print("Couldn't close the issue:", repr(e))
        elif (
            (dt.utcnow() - issue.updated_at.replace(tzinfo=None)).days > 23
            and (dt.utcnow() - issue.created_at.replace(tzinfo=None)).days >= 30
            and not any(label.name.lower() in LABELS_TO_EXEMPT for label in issue.get_labels())
        ):
            # print(f"Would add stale comment to {issue.number}")
            try:
                issue.create_comment(
                    "This issue has been automatically marked as stale because it has not had "
                    "recent activity. If you think this still needs to be addressed "
                    "please comment on this thread.\n\nPlease note that issues that do not follow the "
                    "[contributing guidelines](https://github.com/huggingface/transformers/blob/main/CONTRIBUTING.md) "
                    "are likely to be ignored."
                )
            except github.GithubException as e:
                print("Couldn't create comment:", repr(e))