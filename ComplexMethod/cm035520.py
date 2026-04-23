async def test_get_hooks_returns_hook_events(self):
        conversation_id = uuid4()
        sandbox_id = str(uuid4())
        working_dir = '/workspace'

        mock_conversation = AppConversation(
            id=conversation_id,
            created_by_user_id='test-user',
            sandbox_id=sandbox_id,
            selected_repository='owner/repo',
            sandbox_status=SandboxStatus.RUNNING,
        )

        mock_sandbox = SandboxInfo(
            id=sandbox_id,
            created_by_user_id='test-user',
            status=SandboxStatus.RUNNING,
            sandbox_spec_id=str(uuid4()),
            session_api_key='test-api-key',
            exposed_urls=[
                ExposedUrl(name=AGENT_SERVER, url='http://agent-server:8000', port=8000)
            ],
        )

        mock_sandbox_spec = SandboxSpecInfo(
            id=str(uuid4()), command=None, working_dir=working_dir
        )

        mock_app_conversation_service = MagicMock()
        mock_app_conversation_service.get_app_conversation = AsyncMock(
            return_value=mock_conversation
        )

        mock_sandbox_service = MagicMock()
        mock_sandbox_service.get_sandbox = AsyncMock(return_value=mock_sandbox)

        mock_sandbox_spec_service = MagicMock()
        mock_sandbox_spec_service.get_sandbox_spec = AsyncMock(
            return_value=mock_sandbox_spec
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            'hook_config': {
                'stop': [
                    {
                        'matcher': '*',
                        'hooks': [
                            {
                                'type': 'command',
                                'command': '.openhands/hooks/on_stop.sh',
                                'timeout': 60,
                                'async': True,
                            }
                        ],
                    }
                ]
            }
        }

        mock_httpx_client = AsyncMock(spec=httpx.AsyncClient)
        mock_httpx_client.post = AsyncMock(return_value=mock_response)

        response = await get_conversation_hooks(
            conversation_id=conversation_id,
            app_conversation_service=mock_app_conversation_service,
            sandbox_service=mock_sandbox_service,
            sandbox_spec_service=mock_sandbox_spec_service,
            httpx_client=mock_httpx_client,
        )

        assert response.status_code == status.HTTP_200_OK

        data = __import__('json').loads(response.body.decode('utf-8'))
        assert 'hooks' in data
        assert data['hooks']
        assert data['hooks'][0]['event_type'] == 'stop'
        assert data['hooks'][0]['matchers'][0]['matcher'] == '*'
        assert data['hooks'][0]['matchers'][0]['hooks'][0]['type'] == 'command'
        assert (
            data['hooks'][0]['matchers'][0]['hooks'][0]['command']
            == '.openhands/hooks/on_stop.sh'
        )
        assert data['hooks'][0]['matchers'][0]['hooks'][0]['async'] is True
        assert 'async_' not in data['hooks'][0]['matchers'][0]['hooks'][0]

        mock_httpx_client.post.assert_called_once()
        called_url = mock_httpx_client.post.call_args[0][0]
        assert called_url == 'http://agent-server:8000/api/hooks'