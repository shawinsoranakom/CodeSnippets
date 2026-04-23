async def test_get_user_by_id_success(async_session_maker):
    """
    GIVEN: A user exists in the database
    WHEN: get_user_by_id is called with the user's ID
    THEN: The user is returned with correct data
    """
    # Arrange
    async with async_session_maker() as session:
        org = Org(name='test-org')
        session.add(org)
        await session.flush()

        user = User(
            id=uuid.uuid4(),
            current_org_id=org.id,
            language='en',
            user_consents_to_analytics=True,
            enable_sound_notifications=False,
            git_user_name='testuser',
            git_user_email='test@example.com',
        )
        session.add(user)
        await session.commit()
        user_id = str(user.id)

        # Act - create store with the session
        store = UserAppSettingsStore(db_session=session)
        result = await store.get_user_by_id(user_id)

    # Assert
    assert result is not None
    assert str(result.id) == user_id
    assert result.language == 'en'
    assert result.user_consents_to_analytics is True
    assert result.enable_sound_notifications is False
    assert result.git_user_name == 'testuser'
    assert result.git_user_email == 'test@example.com'