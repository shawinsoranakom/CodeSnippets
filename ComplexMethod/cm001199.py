async def test_get_library_agents(mocker):
    # Mock data
    mock_user_created = [
        prisma.models.AgentGraph(
            id="agent1",
            version=1,
            name="Test Agent 1",
            description="Test Description 1",
            userId="test-user",
            isActive=True,
            createdAt=datetime.now(),
        )
    ]

    mock_library_agents = [
        prisma.models.LibraryAgent(
            id="ua1",
            userId="test-user",
            agentGraphId="agent2",
            settings="{}",  # type: ignore
            agentGraphVersion=1,
            isCreatedByUser=False,
            isDeleted=False,
            isArchived=False,
            createdAt=datetime.now(),
            updatedAt=datetime.now(),
            isFavorite=False,
            useGraphIsActiveVersion=True,
            AgentGraph=prisma.models.AgentGraph(
                id="agent2",
                version=1,
                name="Test Agent 2",
                description="Test Description 2",
                userId="other-user",
                isActive=True,
                createdAt=datetime.now(),
            ),
        )
    ]

    # Mock prisma calls
    mock_agent_graph = mocker.patch("prisma.models.AgentGraph.prisma")
    mock_agent_graph.return_value.find_many = mocker.AsyncMock(
        return_value=mock_user_created
    )

    mock_library_agent = mocker.patch("prisma.models.LibraryAgent.prisma")
    mock_library_agent.return_value.find_many = mocker.AsyncMock(
        return_value=mock_library_agents
    )
    mock_library_agent.return_value.count = mocker.AsyncMock(return_value=1)

    mocker.patch(
        "backend.api.features.library.db._fetch_execution_counts",
        new=mocker.AsyncMock(return_value={}),
    )

    # Call function
    result = await db.list_library_agents("test-user")

    # Verify results
    assert len(result.agents) == 1
    assert result.agents[0].id == "ua1"
    assert result.agents[0].name == "Test Agent 2"
    assert result.agents[0].description == "Test Description 2"
    assert result.agents[0].graph_id == "agent2"
    assert result.agents[0].graph_version == 1
    assert result.agents[0].can_access_graph is False
    assert result.agents[0].is_latest_version is True
    assert result.pagination.total_items == 1
    assert result.pagination.total_pages == 1
    assert result.pagination.current_page == 1
    assert result.pagination.page_size == 50