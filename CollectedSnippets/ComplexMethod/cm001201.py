async def test_list_favorite_library_agents(mocker):
    mock_library_agents = [
        prisma.models.LibraryAgent(
            id="fav1",
            userId="test-user",
            agentGraphId="agent-fav",
            settings="{}",  # type: ignore
            agentGraphVersion=1,
            isCreatedByUser=False,
            isDeleted=False,
            isArchived=False,
            createdAt=datetime.now(),
            updatedAt=datetime.now(),
            isFavorite=True,
            useGraphIsActiveVersion=True,
            AgentGraph=prisma.models.AgentGraph(
                id="agent-fav",
                version=1,
                name="Favorite Agent",
                description="My Favorite",
                userId="other-user",
                isActive=True,
                createdAt=datetime.now(),
            ),
        )
    ]

    mock_library_agent = mocker.patch("prisma.models.LibraryAgent.prisma")
    mock_library_agent.return_value.find_many = mocker.AsyncMock(
        return_value=mock_library_agents
    )
    mock_library_agent.return_value.count = mocker.AsyncMock(return_value=1)

    mocker.patch(
        "backend.api.features.library.db._fetch_execution_counts",
        new=mocker.AsyncMock(return_value={"agent-fav": 7}),
    )

    result = await db.list_favorite_library_agents("test-user")

    assert len(result.agents) == 1
    assert result.agents[0].id == "fav1"
    assert result.agents[0].name == "Favorite Agent"
    assert result.agents[0].graph_id == "agent-fav"
    assert result.pagination.total_items == 1
    assert result.pagination.total_pages == 1
    assert result.pagination.current_page == 1
    assert result.pagination.page_size == 50