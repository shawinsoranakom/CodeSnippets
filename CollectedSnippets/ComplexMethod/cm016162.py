def test_script_stacked_bidir_rnn(seq_len, batch, input_size, hidden_size, num_layers):
    inp = torch.randn(seq_len, batch, input_size)
    states = [
        [
            LSTMState(torch.randn(batch, hidden_size), torch.randn(batch, hidden_size))
            for _ in range(2)
        ]
        for _ in range(num_layers)
    ]
    rnn = script_lstm(input_size, hidden_size, num_layers, bidirectional=True)
    out, out_state = rnn(inp, states)
    custom_state = double_flatten_states(out_state)

    # Control: pytorch native LSTM
    lstm = nn.LSTM(input_size, hidden_size, num_layers, bidirectional=True)
    lstm_state = double_flatten_states(states)
    for layer in range(num_layers):
        for direct in range(2):
            index = 2 * layer + direct
            custom_params = list(rnn.parameters())[4 * index : 4 * index + 4]
            for lstm_param, custom_param in zip(lstm.all_weights[index], custom_params):
                if lstm_param.shape != custom_param.shape:
                    raise AssertionError(
                        f"Shape mismatch at layer {layer}, direction {direct}: "
                        f"lstm_param.shape={lstm_param.shape}, custom_param.shape={custom_param.shape}"
                    )
                with torch.no_grad():
                    lstm_param.copy_(custom_param)
    lstm_out, lstm_out_state = lstm(inp, lstm_state)

    if (out - lstm_out).abs().max() >= 1e-5:
        raise AssertionError(
            f"Output mismatch: max diff={(out - lstm_out).abs().max()}"
        )
    if (custom_state[0] - lstm_out_state[0]).abs().max() >= 1e-5:
        raise AssertionError(
            f"Hidden state mismatch: max diff={(custom_state[0] - lstm_out_state[0]).abs().max()}"
        )
    if (custom_state[1] - lstm_out_state[1]).abs().max() >= 1e-5:
        raise AssertionError(
            f"Cell state mismatch: max diff={(custom_state[1] - lstm_out_state[1]).abs().max()}"
        )