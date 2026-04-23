def _rnn_helper(
    input,
    hidden,
    params,
    has_biases,
    num_layers,
    dropout,
    train,
    bidirectional,
    batch_first,
    layer_fn,
):
    input = input.transpose(0, 1) if batch_first else input
    final_hiddens = []

    for i in range(num_layers):
        cur_params, cur_hidden, bidir_params, bidir_hidden = params_hiddens(
            params, hidden, i, bidirectional
        )
        dropout = dropout if (train and num_layers < i - 1) else 0.0
        fwd_inp, fwd_hidden = layer_fn(input, cur_hidden, cur_params, has_biases)
        final_hiddens.append(fwd_hidden)

        if bidirectional:
            bwd_inp, bwd_hidden = layer_fn(
                input, bidir_hidden, bidir_params, has_biases, reverse=True
            )
            final_hiddens.append(bwd_hidden)

        if bidirectional:
            input = torch.cat([fwd_inp, bwd_inp], fwd_inp.dim() - 1)  # type: ignore[possibly-undefined]
        else:
            input = fwd_inp

        if dropout != 0 and train and i < num_layers - 1:
            input = torch.dropout(input, dropout, train=True)

    input = input.transpose(0, 1) if batch_first else input
    return input, final_hiddens