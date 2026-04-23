async def test_pr_comment_v1_injects_context_and_comment_into_initial_user_message(
        self,
        mock_get_app_conversation_service,
        jinja_env,
    ):
        view = GithubPRComment(
            installation_id=123,
            issue_number=7,
            full_repo_name='test-owner/test-repo',
            is_public_repo=False,
            user_info=_build_user_data(),
            raw_payload=MagicMock(),
            conversation_id='conv',
            uuid=None,
            should_extract=False,
            send_summary_instruction=False,
            title='ignored',
            description='ignored',
            previous_comments=[],
            v1_enabled=True,
            comment_body='nit: rename variable',
            comment_id=1001,
            branch_name='feature-branch',
        )

        async def _load_context():
            view.title = 'PR title'
            view.description = 'PR body'
            view.previous_comments = [
                MagicMock(author='bob', created_at='2026-01-01', body='old thread')
            ]

        view._load_resolver_context = AsyncMock(side_effect=_load_context)  # type: ignore[method-assign]
        view.resolved_org_id = None

        fake_service = _FakeAppConversationService()
        mock_get_app_conversation_service.return_value = (
            _fake_app_conversation_service_ctx(fake_service)
        )

        await view._create_v1_conversation(
            jinja_env=jinja_env,
            saas_user_auth=MagicMock(),
            conversation_metadata=_build_conversation_metadata(),
        )

        assert len(fake_service.requests) == 1
        req = fake_service.requests[0]
        assert req.system_message_suffix is None

        text = req.initial_message.content[0].text
        assert 'feature-branch' in text
        assert 'PR title' in text
        assert 'PR body' in text
        assert 'nit: rename variable' in text
        assert 'old thread' in text