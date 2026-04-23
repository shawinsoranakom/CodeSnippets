def _cudnn_rnn(
    input,
    weight,
    weight_stride0,
    weight_buf,
    hx,
    cx,
    mode,
    hidden_size,
    proj_size,
    num_layers,
    batch_first,
    dropout,
    train,
    bidirectional,
    batch_sizes,
    dropout_state,
):
    is_input_packed = len(batch_sizes) != 0
    if is_input_packed:
        seq_length = len(batch_sizes)
        mini_batch = batch_sizes[0]
        batch_sizes_sum = input.shape[0]
    else:
        seq_length = input.shape[1] if batch_first else input.shape[0]
        mini_batch = input.shape[0] if batch_first else input.shape[1]
        batch_sizes_sum = -1

    num_directions = 2 if bidirectional else 1
    out_size = proj_size if proj_size != 0 else hidden_size
    if is_input_packed:
        out_shape = [batch_sizes_sum, out_size * num_directions]
    else:
        out_shape = (
            [mini_batch, seq_length, out_size * num_directions]
            if batch_first
            else [seq_length, mini_batch, out_size * num_directions]
        )
    output = input.new_empty(out_shape)

    cell_shape = [num_layers * num_directions, mini_batch, hidden_size]
    if cx is None:
        cy = torch.empty(0, device=input.device)
    else:
        cy = cx.new_empty(cell_shape)

    hy = hx.new_empty([num_layers * num_directions, mini_batch, out_size])

    # TODO: Query cudnnGetRNNTrainingReserveSize (expose to python)
    reserve_shape = 0 if train else 0
    reserve = input.new_empty(reserve_shape, dtype=torch.uint8)

    return output, hy, cy, reserve, weight_buf