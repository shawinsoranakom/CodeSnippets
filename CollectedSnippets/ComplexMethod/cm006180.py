async def load_and_prepare_flow(client: AsyncClient, created_api_key):
    """Load a flow template, create it, and wait for it to be ready."""
    # Set up headers
    headers = {"x-api-key": created_api_key.api_key}

    # Create OPENAI_API_KEY global variable
    from tests.api_keys import get_openai_api_key

    try:
        openai_api_key = get_openai_api_key()
    except ValueError:
        pytest.skip("OPENAI_API_KEY environment variable not set")

    await create_global_variable(client, headers, "OPENAI_API_KEY", openai_api_key)

    # Load the Basic Prompting template
    template_path = (
        pathlib.Path(__file__).resolve().parent.parent.parent
        / "base"
        / "langflow"
        / "initial_setup"
        / "starter_projects"
        / "Basic Prompting.json"
    )

    flow_data = await asyncio.to_thread(lambda: json.loads(pathlib.Path(template_path).read_text()))

    # Configure the LanguageModelComponent with an OpenAI model
    # The template has an empty model selection, so we need to set it programmatically
    openai_model_config = [
        {
            "name": "gpt-4o-mini",
            "icon": "OpenAI",
            "category": "OpenAI",
            "provider": "OpenAI",
            "metadata": {
                "context_length": 128000,
                "model_class": "ChatOpenAI",
                "model_name_param": "model",
                "api_key_param": "api_key",
            },
        }
    ]

    # Find and configure the LanguageModelComponent node
    for node in flow_data.get("data", {}).get("nodes", []):
        if node.get("data", {}).get("type") == "LanguageModelComponent":
            node["data"]["node"]["template"]["model"]["value"] = openai_model_config
            # Also set the API key directly in the component template
            node["data"]["node"]["template"]["api_key"]["value"] = openai_api_key
            logger.info("Configured LanguageModelComponent with gpt-4o-mini and API key")
            break

    # Add the flow
    response = await client.post("/api/v1/flows/", json=flow_data, headers=headers)
    logger.info(f"Flow creation response: {response.status_code}")

    assert response.status_code == 201
    flow = response.json()

    # Poll for flow builds to complete
    max_attempts = 10
    for attempt in range(max_attempts):
        # Get the flow builds
        builds_response = await client.get(f"/api/v1/monitor/builds?flow_id={flow['id']}", headers=headers)

        if builds_response.status_code == 200:
            builds = builds_response.json().get("vertex_builds", {})
            # Check if builds are complete
            all_valid = True
            for build_list in builds.values():
                if not build_list or build_list[0].get("valid") is not True:
                    all_valid = False
                    break

            if all_valid and builds:
                logger.info(f"Flow builds completed successfully after {attempt + 1} attempts")
                break

        # Wait before polling again
        if attempt < max_attempts - 1:
            logger.info(f"Waiting for flow builds to complete (attempt {attempt + 1}/{max_attempts})...")
            await asyncio.sleep(1)
    else:
        logger.warning("Flow builds polling timed out, proceeding anyway")

    return flow, headers