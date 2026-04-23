async def test_get_skills_returns_repo_and_knowledge_skills(self):
        """Test successful retrieval of both repo and knowledge skills.

        Arrange: Setup conversation, sandbox, and skills with different types
        Act: Call get_conversation_skills endpoint
        Assert: Response contains both repo and knowledge skills with correct types
        """
        # Arrange
        conversation_id = uuid4()
        sandbox_id = str(uuid4())
        working_dir = '/workspace'

        # Create mock conversation
        mock_conversation = AppConversation(
            id=conversation_id,
            created_by_user_id='test-user',
            sandbox_id=sandbox_id,
            selected_repository='owner/repo',
            sandbox_status=SandboxStatus.RUNNING,
        )

        # Create mock sandbox with agent server URL
        mock_sandbox = SandboxInfo(
            id=sandbox_id,
            created_by_user_id='test-user',
            status=SandboxStatus.RUNNING,
            sandbox_spec_id=str(uuid4()),
            session_api_key='test-api-key',
            exposed_urls=[
                ExposedUrl(name=AGENT_SERVER, url='http://localhost:8000', port=8000)
            ],
        )

        # Create mock sandbox spec
        mock_sandbox_spec = SandboxSpecInfo(
            id=str(uuid4()), command=None, working_dir=working_dir
        )

        # Create mock skills - repo skill (no trigger)
        repo_skill = Skill(
            name='repo_skill',
            content='Repository skill content',
            trigger=None,
        )

        # Create mock skills - knowledge skill (with KeywordTrigger)
        knowledge_skill = Skill(
            name='knowledge_skill',
            content='Knowledge skill content',
            trigger=KeywordTrigger(keywords=['test', 'help']),
        )

        # Mock services
        mock_user_context = MagicMock(spec=UserContext)
        mock_app_conversation_service = _make_service_mock(
            user_context=mock_user_context,
            conversation_return=mock_conversation,
            skills_return=[repo_skill, knowledge_skill],
        )

        mock_sandbox_service = MagicMock()
        mock_sandbox_service.get_sandbox = AsyncMock(return_value=mock_sandbox)

        mock_sandbox_spec_service = MagicMock()
        mock_sandbox_spec_service.get_sandbox_spec = AsyncMock(
            return_value=mock_sandbox_spec
        )

        # Act
        response = await get_conversation_skills(
            conversation_id=conversation_id,
            app_conversation_service=mock_app_conversation_service,
            sandbox_service=mock_sandbox_service,
            sandbox_spec_service=mock_sandbox_spec_service,
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        content = response.body.decode('utf-8')
        import json

        data = json.loads(content)
        assert 'skills' in data
        assert len(data['skills']) == 2

        # Check repo skill
        repo_skill_data = next(
            (s for s in data['skills'] if s['name'] == 'repo_skill'), None
        )
        assert repo_skill_data is not None
        assert repo_skill_data['type'] == 'repo'
        assert repo_skill_data['content'] == 'Repository skill content'
        assert repo_skill_data['triggers'] == []

        # Check knowledge skill
        knowledge_skill_data = next(
            (s for s in data['skills'] if s['name'] == 'knowledge_skill'), None
        )
        assert knowledge_skill_data is not None
        assert knowledge_skill_data['type'] == 'knowledge'
        assert knowledge_skill_data['content'] == 'Knowledge skill content'
        assert knowledge_skill_data['triggers'] == ['test', 'help']