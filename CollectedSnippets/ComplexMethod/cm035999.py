def _count_openhands_activity(
        self, commits: list, review_comments: list, pr_comments: list
    ) -> tuple[int, int, int]:
        """Count OpenHands commits, review comments, and general PR comments"""
        openhands_commit_count = 0
        openhands_review_comment_count = 0
        openhands_general_comment_count = 0

        # Count commits by OpenHands (check both name and login)
        for commit in commits:
            author = commit.get('author', {})
            author_name = author.get('name', '').lower()
            author_login = (
                author.get('github_login', '').lower()
                if author.get('github_login')
                else ''
            )

            if self._check_openhands_author(author_name, author_login):
                openhands_commit_count += 1

        # Count review comments by OpenHands
        for review_comment in review_comments:
            author_login = (
                review_comment.get('author', '').lower()
                if review_comment.get('author')
                else ''
            )
            author_name = ''  # Initialize to avoid reference before assignment
            if self._check_openhands_author(author_name, author_login):
                openhands_review_comment_count += 1

        # Count general PR comments by OpenHands
        for pr_comment in pr_comments:
            author_login = (
                pr_comment.get('author', '').lower() if pr_comment.get('author') else ''
            )
            author_name = ''  # Initialize to avoid reference before assignment
            if self._check_openhands_author(author_name, author_login):
                openhands_general_comment_count += 1

        return (
            openhands_commit_count,
            openhands_review_comment_count,
            openhands_general_comment_count,
        )