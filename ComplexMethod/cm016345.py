def get_prediction_confidence(self, tests: list[str]) -> TestPrioritizations:
        try:
            commit_messages = get_git_commit_info()
        except Exception as e:
            print(f"Can't get commit info due to {e}")
            commit_messages = ""
        try:
            pr_number = get_pr_number()
            if pr_number is not None:
                pr_body = get_issue_or_pr_body(pr_number)
            else:
                pr_body = ""
        except Exception as e:
            print(f"Can't get PR body due to {e}")
            pr_body = ""

        # Search for linked issues or PRs
        linked_issue_bodies: list[str] = []
        for issue in self._search_for_linked_issues(
            commit_messages
        ) + self._search_for_linked_issues(pr_body):
            try:
                linked_issue_bodies.append(get_issue_or_pr_body(int(issue)))
            except Exception:
                pass

        mentioned = []
        for test in tests:
            if (
                test in commit_messages
                or test in pr_body
                or any(test in body for body in linked_issue_bodies)
            ):
                mentioned.append(test)

        return TestPrioritizations(tests, {TestRun(test): 1 for test in mentioned})