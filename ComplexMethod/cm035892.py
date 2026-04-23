async def test_store_updates_org_defaults_and_all_members_for_shared_keys(
    session_maker, async_session_maker, mock_config, org_with_multiple_members_fixture
):
    """External provider keys should still sync as an org-wide shared snapshot."""
    from sqlalchemy import select
    from storage.org import Org
    from storage.org_member import OrgMember

    fixture = org_with_multiple_members_fixture
    org_id = fixture['org_id']
    decrypt_value = fixture['decrypt_value']

    store = SaasSettingsStore(str(fixture['admin_user_id']), mock_config)
    new_settings = _make_settings(
        model='anthropic/claude-sonnet-4',
        base_url='https://api.anthropic.com/v1',
        max_iterations=100,
        api_key='shared-external-api-key',
    )

    with patch('storage.saas_settings_store.a_session_maker', async_session_maker):
        await store.store(new_settings)

    with session_maker() as session:
        org = session.execute(select(Org).where(Org.id == org_id)).scalars().first()
        assert org is not None
        assert org.agent_settings['llm']['model'] == 'anthropic/claude-sonnet-4'
        assert org.agent_settings['llm']['base_url'] == 'https://api.anthropic.com/v1'
        assert org.conversation_settings['max_iterations'] == 100

        members = {
            str(member.user_id): member
            for member in session.execute(
                select(OrgMember).where(OrgMember.org_id == org_id)
            )
            .scalars()
            .all()
        }
        assert len(members) == 3

        for member in members.values():
            assert (
                member.agent_settings_diff['llm']['model']
                == 'anthropic/claude-sonnet-4'
            )
            assert (
                member.agent_settings_diff['llm']['base_url']
                == 'https://api.anthropic.com/v1'
            )
            assert member.conversation_settings_diff['max_iterations'] == 100
            assert decrypt_value(member._llm_api_key) == 'shared-external-api-key'