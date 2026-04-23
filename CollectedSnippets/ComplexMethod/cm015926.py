def test_graph_provenance(self):
        def check_node_source(node_source_dict, name, pass_name, action):
            self.assertEqual(node_source_dict["name"], name)
            self.assertEqual(node_source_dict["pass_name"], pass_name)
            self.assertEqual(node_source_dict["action"], action)

        def get_first_node_source_and_check(node_source_dict):
            """
            Get the first node source from the from_node list.
            """
            self.assertEqual(len(node_source_dict["from_node"]), 1)
            return node_source_dict["from_node"][0]

        class Model(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.fc1 = torch.nn.Linear(10, 16)
                self.relu = torch.nn.ReLU()
                self.fc2 = torch.nn.Linear(16, 1)
                self.sigmoid = torch.nn.Sigmoid()

            def forward(self, x):
                x = self.fc1(x)
                x = self.relu(x)
                x = self.fc2(x)
                x = self.sigmoid(x)
                return (x,)

        model = Model()
        example_inputs = (torch.randn(8, 10),)
        ep = torch.export.export(model, example_inputs, strict=True)

        decomposed_ep = ep.run_decompositions(default_decompositions())
        # node decomposed from same ancestor node should have same from_node info
        for node in decomposed_ep.graph.nodes:
            if node.op not in {"placeholder", "output"}:
                if "from_node" not in node.meta:
                    raise AssertionError(
                        f"Expected 'from_node' in node.meta for node {node.name}"
                    )

        node_name_to_from_node = {
            node.name: node.meta["from_node"]
            for node in decomposed_ep.graph.nodes
            if node.op not in {"placeholder", "output"}
        }
        same_ancestor_nodes = {
            "permute": "addmm",
            "addmm": "permute",
            "permute_1": "addmm_1",
            "addmm_1": "permute_1",
        }

        for node_name_1 in node_name_to_from_node:
            for node_name_2 in node_name_to_from_node:
                if node_name_2 in {
                    node_name_1,
                    same_ancestor_nodes.get(node_name_1),
                }:
                    self.assertEqual(
                        node_name_to_from_node[node_name_1],
                        node_name_to_from_node[node_name_2],
                    )
                    self.assertEqual(
                        [
                            NodeSource._from_dict(ns.to_dict())
                            for ns in node_name_to_from_node[node_name_1]
                        ],
                        node_name_to_from_node[node_name_2],
                    )
                else:
                    self.assertNotEqual(
                        node_name_to_from_node[node_name_1],
                        node_name_to_from_node[node_name_2],
                    )
                    self.assertNotEqual(
                        [
                            NodeSource._from_dict(ns.to_dict())
                            for ns in node_name_to_from_node[node_name_1]
                        ],
                        node_name_to_from_node[node_name_2],
                    )

        gm = ep.module()
        provenance = get_graph_provenance_json(gm.graph)
        self.assertEqual(
            set(provenance.keys()), {"relu", "linear", "sigmoid", "linear_1"}
        )

        # Check node "linear" is created from node "x" in PropagateUnbackedSymInts
        key_provenance = provenance["linear"][0]["from_node"]
        self.assertEqual(len(key_provenance), 1)
        key_provenance = key_provenance[0]
        check_node_source(
            key_provenance,
            "x",
            "Interpreter_PropagateUnbackedSymInts",
            CREATE_STR,
        )

        # Check node "x" is then created from another node "x" in FlattenInputOutputSignature
        key_provenance = get_first_node_source_and_check(key_provenance)
        check_node_source(
            key_provenance,
            "x",
            "Interpreter_DynamoGraphTransformer",
            CREATE_STR,
        )

        gm, graph_signature = aot_export_module(
            gm,
            example_inputs,
            trace_joint=False,
        )

        provenance = get_graph_provenance_json(gm.graph)

        self.assertEqual(
            set(provenance.keys()), {"t", "addmm", "relu", "t_1", "addmm_1", "sigmoid"}
        )
        for key in ["t", "addmm"]:
            # The node provenance hierarchy should be:
            # t -> linear -> x -> x
            #
            # x -> y means x is created from y

            key_provenance = provenance[key]
            self.assertEqual(len(key_provenance), 1)
            key_provenance = key_provenance[0]

            # Check node "t" and "addmm" is created from node "linear" in PropagateUnbackedSymInts
            check_node_source(
                key_provenance,
                "linear",
                "Interpreter_PropagateUnbackedSymInts",
                CREATE_STR,
            )

            # Check node "linear" is then created from node "x" in PropagateUnbackedSymInts
            key_provenance = get_first_node_source_and_check(key_provenance)[
                "from_node"
            ][0]
            check_node_source(
                key_provenance,
                "x",
                "Interpreter_PropagateUnbackedSymInts",
                CREATE_STR,
            )

            # Check node "x" is then created from another node "x" in FlattenInputOutputSignature
            key_provenance = get_first_node_source_and_check(key_provenance)
            check_node_source(
                key_provenance,
                "x",
                "Interpreter_DynamoGraphTransformer",
                CREATE_STR,
            )