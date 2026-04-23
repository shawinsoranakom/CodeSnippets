async def list_flows_only():
            try:
                import httpx
            except ImportError:
                print("❌ Missing dependency: httpx")
                print("Install with: pip install httpx")
                sys.exit(1)

            # Quick authentication to access the API
            username = "langflow"
            password = "langflow"

            async with httpx.AsyncClient(base_url=args.host, timeout=30.0) as client:
                # Health check
                try:
                    health_response = await client.get("/health")
                    if health_response.status_code != 200:
                        raise Exception(f"Langflow not available at {args.host}")
                except Exception as e:
                    print(f"❌ Cannot connect to Langflow at {args.host}: {e}")
                    sys.exit(1)

                # Login to get access token
                try:
                    login_data = {"username": username, "password": password}
                    login_response = await client.post(
                        "/api/v1/login",
                        data=login_data,
                        headers={"Content-Type": "application/x-www-form-urlencoded"},
                    )

                    if login_response.status_code != 200:
                        raise Exception(f"Authentication failed: {login_response.status_code}")

                    tokens = login_response.json()
                    access_token = tokens["access_token"]

                except Exception as e:
                    print(f"❌ Authentication failed: {e}")
                    print("Make sure Langflow is running with default credentials (langflow/langflow)")
                    sys.exit(1)

                # Get flows from API
                flows = await list_available_flows(args.host, access_token)
                if not flows:
                    print("❌ No starter project flows found!")
                    sys.exit(1)

                print(f"\n{'=' * 80}")
                print("AVAILABLE STARTER PROJECT FLOWS")
                print(f"{'=' * 80}")

                for flow_name, name, description in flows:
                    print(f"📄 {name}")
                    print(f"   Description: {description}")
                    print()

                print(f"Total: {len(flows)} flows available")