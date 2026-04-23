async def test_store_keeps_openhands_managed_keys_member_specific(
    session_maker, async_session_maker, mock_config, org_with_multiple_members_fixture
):
    """Managed OpenHands keys should not be copied from one member to everyone else."""
    from sqlalchemy import select
    from storage.org import Org
    from storage.org_member import OrgMember

    fixture = org_with_multiple_members_fixture
    org_id = fixture['org_id']
    admin_user_id = str(fixture['admin_user_id'])
    decrypt_value = fixture['decrypt_value']

    store = SaasSettingsStore(admin_user_id, mock_config)
    new_settings = _make_settings(
        model='openhands/claude-opus-4-5-20251101',
        base_url=LITE_LLM_API_URL,
        max_iterations=75,
        api_key='admin-managed-api-key',
    )

    with (
        patch('storage.saas_settings_store.a_session_maker', async_session_maker),
        patch(
            'storage.saas_settings_store.LiteLlmManager.verify_existing_key',
            new_callable=AsyncMock,
            return_value=True,
        ),
    ):
        await store.store(new_settings)

    with session_maker() as session:
        org = session.execute(select(Org).where(Org.id == org_id)).scalars().first()
        assert org is not None
        # Settings normalizes openhands/ → litellm_proxy/ during construction
        assert (
            org.agent_settings['llm']['model']
            == 'litellm_proxy/claude-opus-4-5-20251101'
        )
        assert org.agent_settings['llm']['base_url'] == LITE_LLM_API_URL
        assert org.conversation_settings['max_iterations'] == 75

        members = {
            str(member.user_id): member
            for member in session.execute(
                select(OrgMember).where(OrgMember.org_id == org_id)
            )
            .scalars()
            .all()
        }
        assert len(members) == 3

        admin_member = members[admin_user_id]
        assert decrypt_value(admin_member._llm_api_key) == 'admin-managed-api-key'

        member1 = members[str(fixture['member1_user_id'])]
        member2 = members[str(fixture['member2_user_id'])]
        assert decrypt_value(member1._llm_api_key) == 'member1-initial-key'
        assert decrypt_value(member2._llm_api_key) == 'member2-initial-key'

        for member in members.values():
            assert (
                member.agent_settings_diff['llm']['model']
                == 'litellm_proxy/claude-opus-4-5-20251101'
            )
            assert member.agent_settings_diff['llm']['base_url'] == LITE_LLM_API_URL
            assert member.conversation_settings_diff['max_iterations'] == 75