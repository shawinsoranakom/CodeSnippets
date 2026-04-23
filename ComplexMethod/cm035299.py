def guess_success(
        self,
        issue: Issue,
        history: list[Event],
        git_patch: str | None = None,
    ) -> tuple[bool, None | list[bool], str]:
        """Guess if the issue is fixed based on the history, issue description and git patch.

        Args:
            issue: The issue to check
            history: The agent's history
            git_patch: Optional git patch showing the changes made
        """
        last_message = history[-1].message

        issues_context = json.dumps(issue.closing_issues, indent=4)
        success_list = []
        explanation_list = []

        # Handle PRs with file-specific review comments
        if issue.review_threads:
            for review_thread in issue.review_threads:
                if issues_context and last_message:
                    success, explanation = self._check_review_thread(
                        review_thread, issues_context, last_message, git_patch
                    )
                else:
                    success, explanation = False, 'Missing context or message'
                success_list.append(success)
                explanation_list.append(explanation)
        # Handle PRs with only thread comments (no file-specific review comments)
        elif issue.thread_comments:
            if issue.thread_comments and issues_context and last_message:
                success, explanation = self._check_thread_comments(
                    issue.thread_comments, issues_context, last_message, git_patch
                )
            else:
                success, explanation = (
                    False,
                    'Missing thread comments, context or message',
                )
            success_list.append(success)
            explanation_list.append(explanation)
        elif issue.review_comments:
            # Handle PRs with only review comments (no file-specific review comments or thread comments)
            if issue.review_comments and issues_context and last_message:
                success, explanation = self._check_review_comments(
                    issue.review_comments, issues_context, last_message, git_patch
                )
            else:
                success, explanation = (
                    False,
                    'Missing review comments, context or message',
                )
            success_list.append(success)
            explanation_list.append(explanation)
        else:
            # No review comments, thread comments, or file-level review comments found
            return False, None, 'No feedback was found to process'

        # Return overall success (all must be true) and explanations
        if not success_list:
            return False, None, 'No feedback was processed'
        return all(success_list), success_list, json.dumps(explanation_list)