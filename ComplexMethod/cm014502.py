def merge_ghstack_into(
        self,
        repo: GitRepo,
        skip_mandatory_checks: bool,
        comment_id: int | None = None,
        skip_all_rule_checks: bool = False,
    ) -> list[GitHubPR]:
        if not self.is_ghstack_pr():
            raise AssertionError(
                f"merge_ghstack_into called on non-ghstack PR #{self.pr_num}"
            )
        ghstack_prs = get_ghstack_prs(
            repo, self, open_only=False
        )  # raises error if out of sync
        pr_dependencies = []
        for pr, rev in ghstack_prs:
            if pr.is_closed():
                pr_dependencies.append(pr)
                continue

            commit_msg = pr.gen_commit_message(
                filter_ghstack=True, ghstack_deps=pr_dependencies
            )
            if pr.pr_num != self.pr_num and not skip_all_rule_checks:
                # Raises exception if matching rule is not found
                find_matching_merge_rule(
                    pr,
                    repo,
                    skip_mandatory_checks=skip_mandatory_checks,
                    skip_internal_checks=can_skip_internal_checks(self, comment_id),
                )
            repo.cherry_pick(rev)
            repo.amend_commit_message(commit_msg)
            pr_dependencies.append(pr)
        return [x for x, _ in ghstack_prs if not x.is_closed()]