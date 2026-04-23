async def test_store_projects_mixed_new_and_existing(
    repository_store, async_session_maker
):
    """Test storing a mix of new and existing repositories."""
    # Setup - create one existing repository
    existing_repo = StoredRepository(
        repo_name='owner/existing-repo',
        repo_id='github##123',
        is_public=True,
    )

    async with async_session_maker() as session:
        session.add(existing_repo)
        await session.commit()

    # Execute - store a mix of new and existing
    repos_to_store = [
        StoredRepository(
            repo_name='owner/existing-repo',
            repo_id='github##123',
            is_public=False,  # Will update
        ),
        StoredRepository(
            repo_name='owner/new-repo',
            repo_id='github##456',
            is_public=True,
        ),
    ]

    with patch('storage.repository_store.a_session_maker', async_session_maker):
        await repository_store.store_projects(repos_to_store)

    # Verify results
    async with async_session_maker() as session:
        result = await session.execute(
            select(StoredRepository).filter(
                StoredRepository.repo_id.in_(['github##123', 'github##456'])
            )
        )
        repos = result.scalars().all()
        assert len(repos) == 2

        # Check the updated existing repo
        existing = next(r for r in repos if r.repo_id == 'github##123')
        assert existing.repo_name == 'owner/existing-repo'
        assert existing.is_public is False

        # Check the new repo
        new = next(r for r in repos if r.repo_id == 'github##456')
        assert new.repo_name == 'owner/new-repo'
        assert new.is_public is True