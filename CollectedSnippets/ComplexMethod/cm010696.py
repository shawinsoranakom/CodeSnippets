def one_layer_lstm(inp, hidden, params, has_biases, reverse=False):
    ih_weight = params[0]
    hh_weight = params[1]
    ih_bias = params[2] if has_biases else None
    hh_bias = params[3] if has_biases else None
    hr_weight = (
        params[4] if len(params) == 5 else params[2] if len(params) == 3 else None
    )

    hx = hidden[0].unsqueeze(0)
    cx = hidden[1].unsqueeze(0)

    precomputed_input = F.linear(inp, ih_weight, ih_bias)
    precomputed_input = precomputed_input.flip(0) if reverse else precomputed_input
    step_output = []
    for inp in precomputed_input:
        hx, cx = lstm_cell(inp, hx, cx, hh_weight, hh_bias, hr_weight, chunk_dim=2)
        step_output.append(hx)

    if reverse:
        step_output.reverse()

    out = torch.cat(step_output, 0)

    return out, (hx.squeeze(1), cx.squeeze(1))