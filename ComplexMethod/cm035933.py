async def test_get_me_success(self, mock_me_app, test_user_id, test_org_id):
        """GIVEN: Authenticated user who is a member of the organization
        WHEN: GET /api/organizations/{org_id}/me is called
        THEN: Returns 200 with the user's membership data including role name and email
        """
        me_response = self._make_me_response(
            org_id=test_org_id,
            user_id=test_user_id,
            email='owner@example.com',
            role='owner',
            llm_model='gpt-4',
            llm_base_url='https://api.example.com',
            max_iterations=50,
            status_val='active',
        )

        with patch(
            'server.routes.orgs.OrgMemberService.get_me',
            new_callable=AsyncMock,
            return_value=me_response,
        ):
            client = TestClient(mock_me_app)
            response = client.get(f'/api/organizations/{test_org_id}/me')

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['org_id'] == str(test_org_id)
        assert data['user_id'] == test_user_id
        assert data['email'] == 'owner@example.com'
        assert data['role'] == 'owner'
        assert data['agent_settings_diff']['llm']['model'] == 'gpt-4'
        assert (
            data['agent_settings_diff']['llm']['base_url'] == 'https://api.example.com'
        )
        assert data['agent_settings_diff']['max_iterations'] == 50
        assert data['status'] == 'active'