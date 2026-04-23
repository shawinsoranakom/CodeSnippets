def get_and_check_output(output, expected_shape):
    assert output.kv_transfer_params is not None
    hidden_states_path = output.kv_transfer_params.get("hidden_states_path")
    assert hidden_states_path is not None
    assert os.path.exists(hidden_states_path)

    # Load and verify the saved tensors
    with safe_open(hidden_states_path, "pt") as f:
        # Check that token_ids and hidden_states are present
        tensor_names = f.keys()
        assert "token_ids" in tensor_names
        assert "hidden_states" in tensor_names

        token_ids = f.get_tensor("token_ids")
        hidden_states = f.get_tensor("hidden_states")

        prompt_token_ids = output.prompt_token_ids
        assert torch.equal(token_ids, torch.tensor(prompt_token_ids))

        assert hidden_states.shape == expected_shape

        # Verify hidden_states are not all zeros (i.e., they were actually computed)
        assert not torch.allclose(hidden_states, torch.zeros_like(hidden_states))

    return token_ids, hidden_states