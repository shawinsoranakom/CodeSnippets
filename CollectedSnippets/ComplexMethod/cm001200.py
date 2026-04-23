async def test_create_library_agent_uses_upsert():
    """create_library_agent should use upsert (not create) to handle duplicates."""
    mock_graph = MagicMock()
    mock_graph.id = "graph-1"
    mock_graph.version = 1
    mock_graph.user_id = "user-1"
    mock_graph.nodes = []
    mock_graph.sub_graphs = []

    mock_upserted = MagicMock(name="UpsertedLibraryAgent")

    @asynccontextmanager
    async def fake_tx():
        yield None

    with (
        patch("backend.api.features.library.db.transaction", fake_tx),
        patch("prisma.models.LibraryAgent.prisma") as mock_prisma,
        patch(
            "backend.api.features.library.db.add_generated_agent_image",
            new=AsyncMock(),
        ),
        patch(
            "backend.api.features.library.model.LibraryAgent.from_db",
            return_value=MagicMock(),
        ),
    ):
        mock_prisma.return_value.upsert = AsyncMock(return_value=mock_upserted)

        result = await db.create_library_agent(mock_graph, "user-1")

    assert len(result) == 1
    upsert_call = mock_prisma.return_value.upsert.call_args
    assert upsert_call is not None
    # Verify the upsert where clause uses the composite unique key
    where = upsert_call.kwargs["where"]
    assert "userId_agentGraphId_agentGraphVersion" in where
    # Verify the upsert data has both create and update branches
    data = upsert_call.kwargs["data"]
    assert "create" in data
    assert "update" in data
    # Verify update branch restores soft-deleted/archived agents
    assert data["update"]["isDeleted"] is False
    assert data["update"]["isArchived"] is False