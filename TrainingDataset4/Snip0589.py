async def create_test_graphs(self) -> List[Dict[str, Any]]:
        """Create test graphs using the API function."""
        print("Creating test graphs...")

        graphs = []
        for user in self.users:
            num_graphs = random.randint(MIN_GRAPHS_PER_USER, MAX_GRAPHS_PER_USER)

            for graph_num in range(num_graphs):
                # Create a simple graph with nodes and links
                graph_id = str(faker.uuid4())
                nodes = []
                links = []

                # Determine if this should be a DummyInput graph (first 3-4 graphs per user)
                is_dummy_input = graph_num < 4

                # Create nodes based on graph type
                if is_dummy_input:
                    # For dummy input graphs: only GetCurrentTimeBlock
                    node_id = str(faker.uuid4())
                    block = next(
                        b
                        for b in self.agent_blocks
                        if b["name"] == "GetCurrentTimeBlock"
                    )
                    input_default = {"trigger": "start", "format": "%H:%M:%S"}

                    node = Node(
                        id=node_id,
                        block_id=block["id"],
                        input_default=input_default,
                        metadata={"position": {"x": 0, "y": 0}},
                    )
                    nodes.append(node)
                else:
                    # For regular graphs: Create calculator agent pattern with 4 nodes
                    # Node 1: AgentInputBlock for 'a'
                    input_a_id = str(faker.uuid4())
                    input_a_block = next(
                        b for b in self.agent_blocks if b["name"] == "AgentInputBlock"
                    )
                    input_a_node = Node(
                        id=input_a_id,
                        block_id=input_a_block["id"],
                        input_default={
                            "name": "a",
                            "title": None,
                            "value": "",
                            "advanced": False,
                            "description": None,
                            "placeholder_values": [],
                        },
                        metadata={"position": {"x": -1012, "y": 674}},
                    )
                    nodes.append(input_a_node)

                    # Node 2: AgentInputBlock for 'b'
                    input_b_id = str(faker.uuid4())
                    input_b_block = next(
                        b for b in self.agent_blocks if b["name"] == "AgentInputBlock"
                    )
                    input_b_node = Node(
                        id=input_b_id,
                        block_id=input_b_block["id"],
                        input_default={
                            "name": "b",
                            "title": None,
                            "value": "",
                            "advanced": False,
                            "description": None,
                            "placeholder_values": [],
                        },
                        metadata={"position": {"x": -1117, "y": 78}},
                    )
                    nodes.append(input_b_node)

                    # Node 3: CalculatorBlock
                    calc_id = str(faker.uuid4())
                    calc_block = next(
                        b for b in self.agent_blocks if b["name"] == "CalculatorBlock"
                    )
                    calc_node = Node(
                        id=calc_id,
                        block_id=calc_block["id"],
                        input_default={"operation": "Add", "round_result": False},
                        metadata={"position": {"x": -435, "y": 363}},
                    )
                    nodes.append(calc_node)

                    # Node 4: AgentOutputBlock
                    output_id = str(faker.uuid4())
                    output_block = next(
                        b for b in self.agent_blocks if b["name"] == "AgentOutputBlock"
                    )
                    output_node = Node(
                        id=output_id,
                        block_id=output_block["id"],
                        input_default={
                            "name": "result",
                            "title": None,
                            "value": "",
                            "format": "",
                            "advanced": False,
                            "description": None,
                        },
                        metadata={"position": {"x": 402, "y": 0}},
                    )
                    nodes.append(output_node)

                    # Create links between nodes (only for non-dummy graphs with multiple nodes)
                    if len(nodes) >= 4:
                        # Use the actual node IDs from the created nodes instead of our variables
                        actual_input_a_id = nodes[0].id  # First node (input_a)
                        actual_input_b_id = nodes[1].id  # Second node (input_b)
                        actual_calc_id = nodes[2].id  # Third node (calculator)
                        actual_output_id = nodes[3].id  # Fourth node (output)

                        # Link input_a to calculator.a
                        link1 = Link(
                            source_id=actual_input_a_id,
                            sink_id=actual_calc_id,
                            source_name="result",
                            sink_name="a",
                            is_static=True,
                        )
                        links.append(link1)

                        # Link input_b to calculator.b
                        link2 = Link(
                            source_id=actual_input_b_id,
                            sink_id=actual_calc_id,
                            source_name="result",
                            sink_name="b",
                            is_static=True,
                        )
                        links.append(link2)

                        # Link calculator.result to output.value
                        link3 = Link(
                            source_id=actual_calc_id,
                            sink_id=actual_output_id,
                            source_name="result",
                            sink_name="value",
                            is_static=False,
                        )
                        links.append(link3)

                # Create graph object with DummyInput in name if it's a dummy input graph
                graph_name = faker.sentence(nb_words=3)
                if is_dummy_input:
                    graph_name = f"DummyInput {graph_name}"

                graph_name = f"{graph_name} Agents"

                graph = Graph(
                    id=graph_id,
                    name=graph_name,
                    description=faker.text(max_nb_chars=200),
                    nodes=nodes,
                    links=links,
                    is_active=True,
                )

                try:
                    # Use the API function to create graph
                    created_graph = await create_graph(graph, user["id"])
                    graph_dict = created_graph.model_dump()
                    # Ensure userId is included for store submissions
                    graph_dict["userId"] = user["id"]
                    graphs.append(graph_dict)
                    print(
                        f"✅ Created graph for user {user['id']}: {graph_dict['name']}"
                    )
                except Exception as e:
                    print(f"Error creating graph: {e}")
                    continue

        self.agent_graphs = graphs
        return graphs

    async def create_test_library_agents(self) -> List[Dict[str, Any]]:
        """Create test library agents using the API function."""
        print("Creating test library agents...")

        library_agents = []
        for user in self.users:
            num_agents = 10  # Create exactly 10 agents per user

            # Get available graphs for this user
            user_graphs = [
                g for g in self.agent_graphs if g.get("userId") == user["id"]
            ]
            if not user_graphs:
                continue

            # Shuffle and take unique graphs to avoid duplicates
            random.shuffle(user_graphs)
            selected_graphs = user_graphs[: min(num_agents, len(user_graphs))]

            for graph_data in selected_graphs:
                try:
                    # Get the graph model from the database
                    from backend.data.graph import get_graph

                    graph = await get_graph(
                        graph_data["id"],
                        graph_data.get("version", 1),
                        user_id=user["id"],
                    )
                    if graph:
                        # Use the API function to create library agent
                        library_agents.extend(
                            v.model_dump()
                            for v in await create_library_agent(graph, user["id"])
                        )
                except Exception as e:
                    print(f"Error creating library agent: {e}")
                    continue

        self.library_agents = library_agents
        return library_agents
