async def trigger_conversation_starter(message: Message):
        """Trigger a conversation starter when a workflow fails.

        This is the updated version that checks user settings.
        """
        payload = message.message.get('payload', {})
        workflow_payload = payload['workflow_run']
        status = WorkflowRunStatus.COMPLETED

        if workflow_payload['conclusion'] == 'failure':
            status = WorkflowRunStatus.FAILURE
        elif workflow_payload['conclusion'] is None:
            status = WorkflowRunStatus.PENDING

        workflow_run = WorkflowRun(
            id=str(workflow_payload['id']), name=workflow_payload['name'], status=status
        )

        selected_repo = GithubFactory.get_full_repo_name(payload['repository'])
        head_branch = payload['workflow_run']['head_branch']

        # Get the user ID to check their settings
        user_id = None
        try:
            sender_id = payload['sender']['id']
            token_manager = TokenManager()
            user_id = await token_manager.get_user_id_from_idp_user_id(
                sender_id, ProviderType.GITHUB
            )
        except (KeyError, Exception) as e:
            logger.warning(
                f'Failed to get user ID for proactive conversation check: {str(e)}'
            )

        # Check if proactive conversations are enabled for this user
        if not await get_user_proactive_conversation_setting(user_id):
            return False

        def _interact_with_github() -> Issue | None:
            with GithubIntegration(
                auth=Auth.AppAuth(GITHUB_APP_CLIENT_ID, GITHUB_APP_PRIVATE_KEY)
            ) as integration:
                access_token = integration.get_access_token(
                    payload['installation']['id']
                ).token

            with Github(auth=Auth.Token(access_token)) as gh:
                repo = gh.get_repo(selected_repo)
                login = (
                    payload['organization']['login']
                    if 'organization' in payload
                    else payload['sender']['login']
                )

                # See if a pull request is open
                open_pulls = repo.get_pulls(state='open', head=f'{login}:{head_branch}')
                if open_pulls.totalCount > 0:
                    prs = open_pulls.get_page(0)
                    relevant_pr = prs[0]
                    issue = repo.get_issue(number=relevant_pr.number)
                    return issue

            return None

        issue: Issue | None = await call_sync_from_async(_interact_with_github)
        if not issue:
            return False

        incoming_commit = payload['workflow_run']['head_sha']
        latest_sha = GithubFailingAction.get_latest_sha(issue)
        if latest_sha != incoming_commit:
            # Return as this commit is not the latest
            return False

        convo_store = ProactiveConversationStore()
        workflow_group = await convo_store.store_workflow_information(
            provider=ProviderType.GITHUB,
            repo_id=payload['repository']['id'],
            incoming_commit=incoming_commit,
            workflow=workflow_run,
            pr_number=issue.number,
            get_all_workflows=GithubFailingAction.create_retrieve_workflows_callback(
                issue, incoming_commit
            ),
        )

        if not workflow_group:
            return False

        logger.info(
            f'[GitHub] Workflow completed for {selected_repo}#{issue.number} on branch {head_branch}'
        )
        GithubFailingAction.leave_requesting_comment(issue, workflow_group)

        return False