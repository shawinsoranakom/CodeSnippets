async def test_skills_search_returns_skills(test_client, tmp_path):
    """Test that GET /api/v1/skills/search returns a paginated list of skills."""
    global_dir = tmp_path / 'global'
    _write_skill_file(global_dir, 'test_repo', skill_type='repo')
    _write_skill_file(
        global_dir, 'test_knowledge', skill_type='knowledge', triggers=['testword']
    )

    with (
        patch('openhands.app_server.user.skills_router.GLOBAL_SKILLS_DIR', global_dir),
        patch(
            'openhands.app_server.user.skills_router.USER_SKILLS_DIR',
            tmp_path / 'nonexistent',
        ),
    ):
        response = test_client.get('/api/v1/skills/search')

    assert response.status_code == 200
    data = response.json()
    assert 'items' in data
    assert 'next_page_id' in data
    assert len(data['items']) == 2

    # Verify skill structure
    skill_names = [s['name'] for s in data['items']]
    assert 'test_repo' in skill_names
    assert 'test_knowledge' in skill_names

    # Check knowledge skill has triggers
    knowledge_skill = next(s for s in data['items'] if s['name'] == 'test_knowledge')
    assert knowledge_skill['triggers'] == ['testword']
    assert knowledge_skill['type'] == 'knowledge'

    # Check repo skill has no triggers
    repo_skill = next(s for s in data['items'] if s['name'] == 'test_repo')
    assert repo_skill['triggers'] is None
    assert repo_skill['type'] == 'repo'

    # No next page when all results fit
    assert data['next_page_id'] is None