async def test_skills_search_pagination(test_client, tmp_path):
    """Test cursor-based pagination."""
    global_dir = tmp_path / 'global'
    _write_skill_file(global_dir, 'skill_a', skill_type='repo')
    _write_skill_file(global_dir, 'skill_b', skill_type='repo')
    _write_skill_file(global_dir, 'skill_c', skill_type='repo')

    with (
        patch('openhands.app_server.user.skills_router.GLOBAL_SKILLS_DIR', global_dir),
        patch(
            'openhands.app_server.user.skills_router.USER_SKILLS_DIR',
            tmp_path / 'nonexistent',
        ),
    ):
        # First page with limit=2
        response = test_client.get('/api/v1/skills/search', params={'limit': 2})
        assert response.status_code == 200
        data = response.json()
        assert len(data['items']) == 2
        assert data['items'][0]['name'] == 'skill_a'
        assert data['items'][1]['name'] == 'skill_b'
        assert data['next_page_id'] == 'skill_b'

        # Second page using next_page_id
        response = test_client.get(
            '/api/v1/skills/search',
            params={'limit': 2, 'page_id': data['next_page_id']},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data['items']) == 1
        assert data['items'][0]['name'] == 'skill_c'
        assert data['next_page_id'] is None