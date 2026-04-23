def gen_commit_message(
        self,
        filter_ghstack: bool = False,
        ghstack_deps: list[GitHubPR] | None = None,
    ) -> str:
        """Fetches title and body from PR description
        adds reviewed by, pull request resolved and optionally
        filters out ghstack info"""
        # Adding the url here makes it clickable within the Github UI
        approved_by_urls = ", ".join(
            prefix_with_github_url(login) for login in self.get_approved_by()
        )
        # Remove "cc: " line from the message body
        msg_body = re.sub(RE_PR_CC_LINE, "", self.get_body())
        if filter_ghstack:
            msg_body = re.sub(RE_GHSTACK_DESC, "", msg_body)
        msg = self.get_title() + f" (#{self.pr_num})\n\n"
        msg += msg_body

        msg += f"\nPull Request resolved: {self.get_pr_url()}\n"
        msg += f"Approved by: {approved_by_urls}\n"
        if ghstack_deps:
            msg += f"ghstack dependencies: {', '.join([f'#{pr.pr_num}' for pr in ghstack_deps])}\n"

        # Mention PR co-authors, which should be at the end of the message
        # And separated from the body by two newlines
        first_coauthor = True
        for author_login, author_name in self.get_authors().items():
            if author_login != self.get_pr_creator_login():
                if first_coauthor:
                    msg, first_coauthor = (msg + "\n", False)
                msg += f"\nCo-authored-by: {author_name}"

        return msg