def merge_changes_locally(
        self,
        repo: GitRepo,
        skip_mandatory_checks: bool = False,
        comment_id: int | None = None,
        branch: str | None = None,
        skip_all_rule_checks: bool = False,
    ) -> list[GitHubPR]:
        """
        :param skip_all_rule_checks: If true, skips all rule checks on ghstack PRs, useful for dry-running merge locally
        """
        branch_to_merge_into = self.default_branch() if branch is None else branch
        if repo.current_branch() != branch_to_merge_into:
            repo.checkout(branch_to_merge_into)

        # It's okay to skip the commit SHA check for ghstack PRs since
        # authoring requires write access to the repo.
        if self.is_ghstack_pr():
            return self.merge_ghstack_into(
                repo,
                skip_mandatory_checks,
                comment_id=comment_id,
                skip_all_rule_checks=skip_all_rule_checks,
            )

        msg = self.gen_commit_message()
        pr_branch_name = f"__pull-request-{self.pr_num}__init__"

        # Determine which commit SHA to merge
        commit_to_merge = None
        if not comment_id:
            raise ValueError("Must provide --comment-id when merging regular PRs")

        # Get the commit SHA that was present when the comment was made
        commit_to_merge = self.get_commit_sha_at_comment(comment_id)
        if not commit_to_merge:
            raise RuntimeError(
                f"Could not find commit that was pushed before comment {comment_id}"
            )

        # Validate that this commit is the latest commit on the PR
        latest_commit = self.last_commit_sha()
        if commit_to_merge != latest_commit:
            raise RuntimeError(
                f"Commit {commit_to_merge} was HEAD when comment {comment_id} was posted "
                f"but now the latest commit on the PR is {latest_commit}. "
                f"Please re-issue the merge command to merge the latest commit."
            )

        print(f"Merging commit {commit_to_merge} locally")

        repo.fetch(commit_to_merge, pr_branch_name)
        repo._run_git("merge", "--squash", pr_branch_name)
        repo._run_git("commit", f'--author="{self.get_author()}"', "-m", msg)

        # Did the PR change since we started the merge?
        pulled_sha = repo.show_ref(pr_branch_name)
        latest_pr_status = GitHubPR(self.org, self.project, self.pr_num)
        if (
            pulled_sha != latest_pr_status.last_commit_sha()
            or pulled_sha != commit_to_merge
        ):
            raise RuntimeError(
                "PR has been updated since CI checks last passed. Please rerun the merge command."
            )
        return []