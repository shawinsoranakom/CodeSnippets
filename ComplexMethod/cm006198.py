def test_handle_message_data_inputs(self, run_flow_component):
        """Test that RunFlow handles Message and Data objects as inputs."""
        # Setup inputs with Message and Data objects
        message_input = Message(text="Hello from Message")
        data_input = Data(data={"text": "Hello from Data"})

        # Simulate ioputs structure
        ioputs = {
            "node_1": {"input_value": message_input},
            "node_2": {"input_value": data_input},
            "node_3": {"input_value": "Plain string"},
        }

        inputs = run_flow_component._build_inputs_from_ioputs(ioputs)

        # Check inputs
        assert len(inputs) == 3

        # Verify Message input conversion
        msg_input = next(i for i in inputs if i["components"] == ["node_1"])
        assert msg_input["input_value"] == "Hello from Message"

        # Verify Data input conversion
        data_in = next(i for i in inputs if i["components"] == ["node_2"])
        assert data_in["input_value"] == "Hello from Data"

        # Verify plain string input
        str_in = next(i for i in inputs if i["components"] == ["node_3"])
        assert str_in["input_value"] == "Plain string"