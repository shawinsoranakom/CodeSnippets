async def test_store_user_repo_mappings_mixed_new_and_existing(
    user_repo_map_store, async_session_maker
):
    """Test storing a mix of new and existing mappings."""
    user_id = str(uuid.uuid4())

    # Setup - create one existing mapping
    existing_mapping = UserRepositoryMap(
        user_id=user_id,
        repo_id='github##123',
        admin=False,
    )

    async with async_session_maker() as session:
        session.add(existing_mapping)
        await session.commit()

    # Execute - store a mix of new and existing
    mappings_to_store = [
        UserRepositoryMap(
            user_id=user_id,
            repo_id='github##123',
            admin=True,  # Will update
        ),
        UserRepositoryMap(
            user_id=user_id,
            repo_id='github##456',
            admin=True,
        ),
    ]

    with patch('storage.user_repo_map_store.a_session_maker', async_session_maker):
        await user_repo_map_store.store_user_repo_mappings(mappings_to_store)

    # Verify results
    async with async_session_maker() as session:
        result = await session.execute(
            select(UserRepositoryMap).filter(
                UserRepositoryMap.repo_id.in_(['github##123', 'github##456'])
            )
        )
        mappings = result.scalars().all()
        assert len(mappings) == 2

        # Check the updated existing mapping
        existing = next(m for m in mappings if m.repo_id == 'github##123')
        assert existing.admin is True

        # Check the new mapping
        new = next(m for m in mappings if m.repo_id == 'github##456')
        assert new.admin is True