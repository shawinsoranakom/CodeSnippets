def test_script_stacked_rnn(seq_len, batch, input_size, hidden_size, num_layers):
    inp = torch.randn(seq_len, batch, input_size)
    states = [
        LSTMState(torch.randn(batch, hidden_size), torch.randn(batch, hidden_size))
        for _ in range(num_layers)
    ]
    rnn = script_lstm(input_size, hidden_size, num_layers)
    out, out_state = rnn(inp, states)
    custom_state = flatten_states(out_state)

    # Control: pytorch native LSTM
    lstm = nn.LSTM(input_size, hidden_size, num_layers)
    lstm_state = flatten_states(states)
    for layer in range(num_layers):
        custom_params = list(rnn.parameters())[4 * layer : 4 * (layer + 1)]
        for lstm_param, custom_param in zip(lstm.all_weights[layer], custom_params):
            if lstm_param.shape != custom_param.shape:
                raise AssertionError(
                    f"Shape mismatch at layer {layer}: lstm_param.shape={lstm_param.shape}, custom_param.shape={custom_param.shape}"
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