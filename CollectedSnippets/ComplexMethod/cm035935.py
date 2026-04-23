async def test_get_or_create_system_api_key_creates_new(
        self, api_key_store, async_session_maker
    ):
        """Test creating a new system API key when none exists."""
        user_id = '5594c7b6-f959-4b81-92e9-b09c206f5081'
        org_id = uuid.UUID('5594c7b6-f959-4b81-92e9-b09c206f5081')
        key_name = 'automation'

        with patch('storage.api_key_store.a_session_maker', async_session_maker):
            api_key = await api_key_store.get_or_create_system_api_key(
                user_id=user_id,
                org_id=org_id,
                name=key_name,
            )

        assert api_key.startswith('sk-oh-')
        assert len(api_key) == len('sk-oh-') + 32

        # Verify the key was created in the database
        async with async_session_maker() as session:
            result = await session.execute(select(ApiKey).filter(ApiKey.key == api_key))
            key_record = result.scalars().first()
            assert key_record is not None
            assert key_record.user_id == user_id
            assert key_record.org_id == org_id
            assert key_record.name == '__SYSTEM__:automation'
            assert key_record.expires_at is None