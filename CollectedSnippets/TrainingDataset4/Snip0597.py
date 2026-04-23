async def main():
    """Main function to load all store agents."""
    print("=" * 60)
    print("Loading Store Agents into Test Database")
    print("=" * 60)

    db = Prisma()
    await db.connect()

    try:
        # Step 0: Initialize agent blocks
        print("\n[Step 0] Initializing agent blocks...")
        known_blocks = await initialize_blocks(db)

        # Step 1: Create user and profile
        print("\n[Step 1] Creating user and profile...")
        await create_user_and_profile(db)

        # Step 2: Load CSV metadata
        print("\n[Step 2] Loading CSV metadata...")
        csv_metadata = await load_csv_metadata()
        print(f"  Found {len(csv_metadata)} store listing entries in CSV")

        # Step 3: Find all JSON files and match with CSV
        print("\n[Step 3] Processing agent JSON files...")
        json_files = list(AGENTS_DIR.glob("agent_*.json"))
        print(f"  Found {len(json_files)} agent JSON files")

        # Build mapping from version_id to json file
        loaded_graphs = {}  # graph_id -> (graph_id, version)
        failed_agents = []

        for json_file in json_files:
            # Extract the version ID from filename (agent_<version_id>.json)
            version_id = json_file.stem.replace("agent_", "")

            if version_id not in csv_metadata:
                print(
                    f"  Warning: {json_file.name} not found in CSV metadata, skipping"
                )
                continue

            metadata = csv_metadata[version_id]
            agent_name = metadata["agent_name"]
            print(f"\nProcessing: {agent_name}")

            # Use a transaction per agent to prevent dangling resources
            try:
                async with db.tx() as tx:
                    # Load and create the agent graph
                    agent_data = await load_agent_json(json_file)
                    graph_id, graph_version = await create_agent_graph(
                        tx, agent_data, known_blocks
                    )
                    loaded_graphs[graph_id] = (graph_id, graph_version)

                    # Create store listing
                    await create_store_listing(tx, graph_id, graph_version, metadata)
            except Exception as e:
                print(f"  Error loading agent '{agent_name}': {e}")
                failed_agents.append(agent_name)
                continue

        # Step 4: Refresh materialized views
        print("\n[Step 4] Refreshing materialized views...")
        try:
            await db.execute_raw("SELECT refresh_store_materialized_views();")
            print("  Materialized views refreshed successfully")
        except Exception as e:
            print(f"  Warning: Could not refresh materialized views: {e}")

        print("\n" + "=" * 60)
        print(f"Successfully loaded {len(loaded_graphs)} agents")
        if failed_agents:
            print(
                f"Failed to load {len(failed_agents)} agents: {', '.join(failed_agents)}"
            )
        print("=" * 60)

    finally:
        await db.disconnect()


def run():
    """Entry point for poetry script."""
    asyncio.run(main())
