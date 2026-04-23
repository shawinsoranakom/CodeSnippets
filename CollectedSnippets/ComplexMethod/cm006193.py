async def load_and_prepare_flow(client: AsyncClient, created_api_key):
    """Load Simple Agent flow and wait for it to be ready."""
    headers = {"x-api-key": created_api_key.api_key}

    # Create OPENAI_API_KEY global variable
    from tests.api_keys import get_openai_api_key

    openai_api_key = get_openai_api_key()
    if not openai_api_key or openai_api_key == "dummy":
        pytest.skip("OPENAI_API_KEY environment variable not set")

    await create_global_variable(client, headers, "OPENAI_API_KEY", openai_api_key)

    # Load the Simple Agent template
    template_path = (
        pathlib.Path(__file__).resolve().parent.parent.parent
        / "base"
        / "langflow"
        / "initial_setup"
        / "starter_projects"
        / "Simple Agent.json"
    )

    flow_data = await asyncio.to_thread(lambda: json.loads(pathlib.Path(template_path).read_text()))

    # Add the flow
    response = await client.post("/api/v1/flows/", json=flow_data, headers=headers)
    assert response.status_code == 201
    flow = response.json()

    # Poll for flow builds to complete
    max_attempts = 10
    for attempt in range(max_attempts):
        builds_response = await client.get(f"/api/v1/monitor/builds?flow_id={flow['id']}", headers=headers)

        if builds_response.status_code == 200:
            builds = builds_response.json().get("vertex_builds", {})
            all_valid = True
            for build_list in builds.values():
                if not build_list or build_list[0].get("valid") is not True:
                    all_valid = False
                    break

            if all_valid and builds:
                break

        if attempt < max_attempts - 1:
            await asyncio.sleep(1)

    return flow, headers