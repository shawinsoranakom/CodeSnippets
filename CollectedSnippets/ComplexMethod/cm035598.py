async def test_skills_search_sorted_by_source_then_name(test_client, tmp_path):
    """Test that skills are sorted by source (global first) then by name."""
    global_dir = tmp_path / 'global'
    user_dir = tmp_path / 'user'

    _write_skill_file(global_dir, 'z_global', skill_type='repo')
    _write_skill_file(global_dir, 'a_global', skill_type='repo')
    _write_skill_file(user_dir, 'b_user', skill_type='repo')

    with (
        patch('openhands.app_server.user.skills_router.GLOBAL_SKILLS_DIR', global_dir),
        patch('openhands.app_server.user.skills_router.USER_SKILLS_DIR', user_dir),
    ):
        response = test_client.get('/api/v1/skills/search')

    assert response.status_code == 200
    data = response.json()
    skills = data['items']

    # Global skills should come first, sorted by name
    assert skills[0]['name'] == 'a_global'
    assert skills[0]['source'] == 'global'
    assert skills[1]['name'] == 'z_global'
    assert skills[1]['source'] == 'global'
    # User skills should come last
    assert skills[2]['name'] == 'b_user'
    assert skills[2]['source'] == 'user'