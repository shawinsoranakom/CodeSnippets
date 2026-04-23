async def create_gitlab_view_from_payload(
        message: Message, token_manager: TokenManager
    ) -> GitlabViewType:
        payload = message.message['payload']
        installation_id = message.message['installation_id']
        user = payload['user']
        user_id = user['id']
        username = user['username']
        repo_obj = payload['project']
        selected_project = repo_obj['path_with_namespace']
        is_public_repo = repo_obj['visibility_level'] == 0
        project_id = payload['object_attributes']['project_id']

        keycloak_user_id = await token_manager.get_user_id_from_idp_user_id(
            user_id, ProviderType.GITLAB
        )

        user_info = UserData(
            user_id=user_id, username=username, keycloak_user_id=keycloak_user_id
        )

        # Check v1_enabled at construction time - this is the source of truth
        v1_enabled = (
            await is_v1_enabled_for_gitlab_resolver(keycloak_user_id)
            if keycloak_user_id
            else False
        )
        logger.info(
            f'[GitLab V1]: User flag found for {keycloak_user_id} is {v1_enabled}'
        )

        if GitlabFactory.is_labeled_issue(message):
            issue_iid = payload['object_attributes']['iid']

            logger.info(
                f'[GitLab] Creating view for labeled issue from {username} in {selected_project}#{issue_iid}'
            )
            return GitlabIssue(
                installation_id=installation_id,
                issue_number=issue_iid,
                project_id=project_id,
                full_repo_name=selected_project,
                is_public_repo=is_public_repo,
                user_info=user_info,
                raw_payload=message,
                conversation_id='',
                should_extract=True,
                send_summary_instruction=True,
                title='',
                description='',
                previous_comments=[],
                is_mr=False,
                v1_enabled=v1_enabled,
            )

        elif GitlabFactory.is_issue_comment(message):
            event_type = payload['event_type']
            issue_iid = payload['issue']['iid']
            object_attributes = payload['object_attributes']
            discussion_id = object_attributes['discussion_id']
            comment_body = object_attributes['note']
            logger.info(
                f'[GitLab] Creating view for issue comment from {username} in {selected_project}#{issue_iid}'
            )

            return GitlabIssueComment(
                installation_id=installation_id,
                comment_body=comment_body,
                issue_number=issue_iid,
                discussion_id=discussion_id,
                project_id=project_id,
                confidential=GitlabFactory.determine_if_confidential(event_type),
                full_repo_name=selected_project,
                is_public_repo=is_public_repo,
                user_info=user_info,
                raw_payload=message,
                conversation_id='',
                should_extract=True,
                send_summary_instruction=True,
                title='',
                description='',
                previous_comments=[],
                is_mr=False,
                v1_enabled=v1_enabled,
            )

        elif GitlabFactory.is_mr_comment(message):
            event_type = payload['event_type']
            merge_request_iid = payload['merge_request']['iid']
            branch_name = payload['merge_request']['source_branch']
            object_attributes = payload['object_attributes']
            discussion_id = object_attributes['discussion_id']
            comment_body = object_attributes['note']
            logger.info(
                f'[GitLab] Creating view for merge request comment from {username} in {selected_project}#{merge_request_iid}'
            )

            return GitlabMRComment(
                installation_id=installation_id,
                comment_body=comment_body,
                issue_number=merge_request_iid,  # Using issue_number as mr_number for compatibility
                discussion_id=discussion_id,
                project_id=project_id,
                full_repo_name=selected_project,
                is_public_repo=is_public_repo,
                user_info=user_info,
                raw_payload=message,
                conversation_id='',
                should_extract=True,
                send_summary_instruction=True,
                confidential=GitlabFactory.determine_if_confidential(event_type),
                branch_name=branch_name,
                title='',
                description='',
                previous_comments=[],
                is_mr=True,
                v1_enabled=v1_enabled,
            )

        elif GitlabFactory.is_mr_comment(message, inline=True):
            event_type = payload['event_type']
            merge_request_iid = payload['merge_request']['iid']
            branch_name = payload['merge_request']['source_branch']
            object_attributes = payload['object_attributes']
            comment_body = object_attributes['note']
            position_info = object_attributes['position']
            discussion_id = object_attributes['discussion_id']
            file_location = object_attributes['position']['new_path']
            line_number = (
                position_info.get('new_line') or position_info.get('old_line') or 0
            )

            logger.info(
                f'[GitLab] Creating view for inline merge request comment from {username} in {selected_project}#{merge_request_iid}'
            )

            return GitlabInlineMRComment(
                installation_id=installation_id,
                issue_number=merge_request_iid,  # Using issue_number as mr_number for compatibility
                discussion_id=discussion_id,
                project_id=project_id,
                full_repo_name=selected_project,
                is_public_repo=is_public_repo,
                user_info=user_info,
                raw_payload=message,
                conversation_id='',
                should_extract=True,
                send_summary_instruction=True,
                confidential=GitlabFactory.determine_if_confidential(event_type),
                branch_name=branch_name,
                file_location=file_location,
                line_number=line_number,
                comment_body=comment_body,
                title='',
                description='',
                previous_comments=[],
                is_mr=True,
                v1_enabled=v1_enabled,
            )

        raise ValueError(f'Unhandled GitLab webhook event: {message}')