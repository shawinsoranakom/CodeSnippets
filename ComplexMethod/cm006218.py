async def setup_langflow_environment(host: str, flow_name: str | None = None, interactive: bool = False) -> dict:
    """Set up complete Langflow environment with real starter project flows."""
    try:
        import httpx
    except ImportError:
        print("❌ Missing dependency: httpx")
        print("Install with: pip install httpx")
        sys.exit(1)

    # Configuration - use default Langflow credentials
    username = "langflow"
    password = "langflow"

    setup_state = {
        "host": host,
        "username": username,
        "password": password,
        "user_id": None,
        "access_token": None,
        "api_key": None,
        "flow_id": None,
        "flow_name": None,
        "flow_data": None,
    }

    async with httpx.AsyncClient(base_url=host, timeout=60.0) as client:
        # Step 1: Health check
        print(f"\n1. Checking Langflow health at {host}...")
        try:
            health_response = await client.get("/health")
            if health_response.status_code != 200:
                raise Exception(f"Health check failed: {health_response.status_code}")
            print("   ✅ Langflow is running and accessible")
        except Exception as e:
            print(f"   ❌ Health check failed: {e}")
            raise

        # Step 2: Skip user creation, use default credentials
        print("2. Using default Langflow credentials...")
        print(f"   ✅ Using username: {username}")

        # Step 3: Login to get JWT token
        print("3. Authenticating...")
        login_data = {
            "username": username,
            "password": password,
        }

        try:
            login_response = await client.post(
                "/api/v1/login",
                data=login_data,  # OAuth2PasswordRequestForm expects form data
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if login_response.status_code != 200:
                raise Exception(f"Login failed: {login_response.status_code} - {login_response.text}")

            tokens = login_response.json()
            setup_state["access_token"] = tokens["access_token"]
            print("   ✅ Authentication successful")
        except Exception as e:
            print(f"   ❌ Authentication failed: {e}")
            raise

        # Step 4: Create API key
        print("4. Creating API key...")
        headers = {"Authorization": f"Bearer {setup_state['access_token']}"}

        try:
            api_key_data = {"name": f"Load Test Key - {int(time.time())}"}
            api_key_response = await client.post("/api/v1/api_key/", json=api_key_data, headers=headers)

            if api_key_response.status_code != 200:
                raise Exception(f"API key creation failed: {api_key_response.status_code} - {api_key_response.text}")

            api_key_info = api_key_response.json()
            setup_state["api_key"] = api_key_info["api_key"]
            print(f"   ✅ API key created: {api_key_info['api_key'][:20]}...")
        except Exception as e:
            print(f"   ❌ API key creation failed: {e}")
            raise

        # Step 5: Select and load flow from API
        print("5. Selecting starter project flow...")

        # Flow selection logic
        selected_flow_name = None
        if interactive:
            selected_flow_name = await select_flow_interactive(host, setup_state["access_token"])
            if not selected_flow_name:
                print("No flow selected. Exiting.")
                sys.exit(0)
        elif flow_name:
            # Verify the flow exists in the API
            flows = await list_available_flows(host, setup_state["access_token"])
            for fname, name, _ in flows:
                if name.lower() == flow_name.lower():
                    selected_flow_name = name
                    break

            if not selected_flow_name:
                print(f"❌ Flow '{flow_name}' not found in starter projects!")
                print("Available flows:")
                for _, name, _ in flows:
                    print(f"  - {name}")
                sys.exit(1)
        else:
            # Default to Basic Prompting
            selected_flow_name = "Basic Prompting"
            print("   Using default flow: Basic Prompting")

        # Get flow data from API
        flow_data = await get_flow_data_by_name(host, setup_state["access_token"], selected_flow_name)
        if not flow_data:
            print(f"❌ Could not load flow data for '{selected_flow_name}'")
            sys.exit(1)

        setup_state["flow_name"] = flow_data.get("name", selected_flow_name)
        setup_state["flow_data"] = flow_data

        print(f"   ✅ Selected flow: {setup_state['flow_name']}")
        print(f"   Description: {flow_data.get('description', 'No description')}")

        # Step 6: Upload the selected flow
        print(f"6. Uploading flow: {setup_state['flow_name']}...")

        try:
            # Prepare flow data for upload
            # Remove the id to let Langflow generate a new one
            flow_upload_data = flow_data.copy()
            if "id" in flow_upload_data:
                del flow_upload_data["id"]

            # Ensure endpoint_name is unique and valid (only letters, numbers, hyphens, underscores)
            import re

            sanitized_name = re.sub(r"[^a-zA-Z0-9_-]", "_", setup_state["flow_name"].lower())
            flow_upload_data["endpoint_name"] = f"loadtest_{int(time.time())}_{sanitized_name}"

            flow_response = await client.post("/api/v1/flows/", json=flow_upload_data, headers=headers)

            if flow_response.status_code != 201:
                raise Exception(f"Flow upload failed: {flow_response.status_code} - {flow_response.text}")

            flow_info = flow_response.json()
            setup_state["flow_id"] = flow_info["id"]
            print("   ✅ Flow uploaded successfully")
            print(f"      Flow ID: {flow_info['id']}")
            print(f"      Endpoint: {flow_info.get('endpoint_name', 'N/A')}")
        except Exception as e:
            print(f"   ❌ Flow upload failed: {e}")
            raise

    return setup_state