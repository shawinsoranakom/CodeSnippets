def get_suggestions(
        failed_jobs: dict, pr_number: int, branch_name: str | None = None
    ) -> str:
        issues = []

        # Collect failing actions with their specific names
        if failed_jobs['actions']:
            failing_actions = failed_jobs['actions']
            issues.append(('GitHub Actions are failing:', False))
            for action in failing_actions:
                issues.append((action, True))

        if any(failed_jobs['merge conflict']):
            issues.append(('There are merge conflicts', False))

        # Format each line with proper indentation and dashes
        formatted_issues = []
        for issue, is_nested in issues:
            if is_nested:
                formatted_issues.append(f'  - {issue}')
            else:
                formatted_issues.append(f'- {issue}')
        issues_text = '\n'.join(formatted_issues)

        # Build list of possible suggestions based on actual issues
        suggestions = []
        branch_info = f' at branch `{branch_name}`' if branch_name else ''

        if any(failed_jobs['merge conflict']):
            suggestions.append(
                f'@OpenHands please fix the merge conflicts on PR #{pr_number}{branch_info}'
            )
        if any(failed_jobs['actions']):
            suggestions.append(
                f'@OpenHands please fix the failing actions on PR #{pr_number}{branch_info}'
            )

        # Take at most 2 suggestions
        suggestions = suggestions[:2]

        help_text = """If you'd like me to help, just leave a comment, like

```
{}
```

Feel free to include any additional details that might help me get this PR into a better state.

<sub><sup>You can manage your notification [settings]({})</sup></sub>""".format(
            '\n```\n\nor\n\n```\n'.join(suggestions), f'{HOST_URL}/settings/app'
        )

        return f'{GithubFailingAction.unqiue_suggestions_header}\n\n{issues_text}\n\n{help_text}'