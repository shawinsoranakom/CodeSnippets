async def is_job_requested(self, message: Message) -> bool:
        self._confirm_incoming_source_type(message)

        installation_id = message.message['installation']
        payload = message.message.get('payload', {})
        repo_obj = payload.get('repository')
        if not repo_obj:
            return False
        username = payload.get('sender', {}).get('login')
        repo_name = self._get_full_repo_name(repo_obj)

        # Suggestions contain `@openhands` macro; avoid kicking off jobs for system recommendations
        if GithubFactory.is_pr_comment(
            message
        ) and GithubFailingAction.unqiue_suggestions_header in payload.get(
            'comment', {}
        ).get('body', ''):
            return False

        # Check event types before making expensive API calls (e.g., _user_has_write_access_to_repo)
        if not (
            GithubFactory.is_labeled_issue(message)
            or GithubFactory.is_issue_comment(message)
            or GithubFactory.is_pr_comment(message)
            or GithubFactory.is_inline_pr_comment(message)
        ):
            return False

        logger.info(f'[GitHub] Checking permissions for {username} in {repo_name}')
        user_has_write_access = self._user_has_write_access_to_repo(
            installation_id, repo_name, username
        )

        if (
            GithubFactory.is_eligible_for_conversation_starter(message)
            and user_has_write_access
        ):
            await GithubFactory.trigger_conversation_starter(message)

        return user_has_write_access