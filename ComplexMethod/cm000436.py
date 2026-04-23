async def test_access_store_listing_graph(server: SpinTestServer):
    """
    Test the access of a store listing graph.
    """
    graph = Graph(
        id="test_clean_graph",
        name="Test Clean Graph",
        description="Test graph cleaning",
        nodes=[
            Node(
                id="input_node",
                block_id=AgentInputBlock().id,
                input_default={
                    "name": "test_input",
                    "value": "test value",
                    "description": "Test input description",
                },
            ),
        ],
        links=[],
    )

    # Create graph and get model
    create_graph = CreateGraph(graph=graph)
    created_graph = await server.agent_server.test_create_graph(
        create_graph, DEFAULT_USER_ID
    )

    # Ensure the default user has a Profile (required for store submissions)
    existing_profile = await prisma.models.Profile.prisma().find_first(
        where={"userId": DEFAULT_USER_ID}
    )
    if not existing_profile:
        await prisma.models.Profile.prisma().create(
            data=prisma.types.ProfileCreateInput(
                userId=DEFAULT_USER_ID,
                name="Default User",
                username=f"default-user-{DEFAULT_USER_ID[:8]}",
                description="Default test user profile",
                links=[],
            )
        )

    store_submission_request = store.StoreSubmissionRequest(
        graph_id=created_graph.id,
        graph_version=created_graph.version,
        slug=created_graph.id,
        name="Test name",
        sub_heading="Test sub heading",
        video_url=None,
        image_urls=[],
        description="Test description",
        categories=[],
    )

    # First we check the graph an not be accessed by a different user
    with pytest.raises(fastapi.exceptions.HTTPException) as exc_info:
        await server.agent_server.test_get_graph(
            created_graph.id,
            created_graph.version,
            "3e53486c-cf57-477e-ba2a-cb02dc828e1b",
        )
    assert exc_info.value.status_code == 404
    assert "Graph" in str(exc_info.value.detail)

    # Now we create a store listing
    store_listing = await server.agent_server.test_create_store_listing(
        store_submission_request, DEFAULT_USER_ID
    )

    if isinstance(store_listing, fastapi.responses.JSONResponse):
        assert False, "Failed to create store listing"

    slv_id = (
        store_listing.listing_version_id
        if store_listing.listing_version_id is not None
        else None
    )

    assert slv_id is not None

    admin_user = await create_test_user(alt_user=True)
    await server.agent_server.test_review_store_listing(
        store.ReviewSubmissionRequest(
            store_listing_version_id=slv_id,
            is_approved=True,
            comments="Test comments",
        ),
        user_id=admin_user.id,
    )

    # Now we check the graph can be accessed by a user that does not own the graph
    got_graph = await server.agent_server.test_get_graph(
        created_graph.id, created_graph.version, "3e53486c-cf57-477e-ba2a-cb02dc828e1b"
    )
    assert got_graph is not None