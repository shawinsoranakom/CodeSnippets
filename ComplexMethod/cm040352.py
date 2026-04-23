def lstm(
    inputs,
    initial_state_h,
    initial_state_c,
    mask,
    kernel,
    recurrent_kernel,
    bias,
    activation,
    recurrent_activation,
    return_sequences=False,
    go_backwards=False,
    unroll=False,
):
    # Masking is not supported by the cuDNN path; fall back to the
    # generic RNN loop which handles masking correctly.
    if mask is not None:
        raise NotImplementedError

    if not cudnn_ok(
        activation,
        recurrent_activation,
        unroll,
        use_bias=bias is not None,
    ):
        raise NotImplementedError

    try:
        from jax.experimental.rnn import lstm as jax_lstm
    except ImportError as e:
        raise NotImplementedError(
            f"jax.experimental.rnn unavailable: {e}"
        ) from e

    input_size = kernel.shape[0]
    hidden_size = recurrent_kernel.shape[0]
    batch_size = inputs.shape[0]

    # Transpose Keras kernels to cuDNN layout and flatten.
    # Gate order [i, f, c, o] matches cuDNN [i, f, g, o].
    W_ih = jnp.asarray(kernel).T
    W_hh = jnp.asarray(recurrent_kernel).T

    if bias is not None:
        b_ih = jnp.asarray(bias)
    else:
        b_ih = jnp.zeros(4 * hidden_size)
    b_hh = jnp.zeros_like(b_ih)

    # cuDNN flat weight order: [W_ih, W_hh, b_ih, b_hh]
    weights = jnp.concatenate(
        [W_ih.ravel(), W_hh.ravel(), b_ih.ravel(), b_hh.ravel()]
    )

    # cuDNN expects (num_layers * num_directions, batch, hidden)
    h_0 = jnp.asarray(initial_state_h)
    c_0 = jnp.asarray(initial_state_c)
    if h_0.ndim == 2:
        h_0 = h_0[jnp.newaxis]
        c_0 = c_0[jnp.newaxis]

    if go_backwards:
        inputs = jnp.flip(inputs, axis=1)

    seq_lengths = jnp.full((batch_size,), inputs.shape[1], dtype=jnp.int32)

    try:
        y, h_n, c_n = jax_lstm(
            inputs,
            h_0,
            c_0,
            weights,
            seq_lengths,
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=1,
            dropout=0.0,
            bidirectional=False,
        )
    except (RuntimeError, TypeError, ValueError) as e:
        raise NotImplementedError(f"cuDNN LSTM failed: {e}") from e

    # y: (batch, seq_len, hidden), h_n/c_n: (1, batch, hidden)
    h_n = h_n.squeeze(0)
    c_n = c_n.squeeze(0)
    last_output = y[:, -1]

    if not return_sequences:
        outputs = last_output[:, jnp.newaxis, :]
    else:
        outputs = y

    if go_backwards and return_sequences:
        outputs = jnp.flip(outputs, axis=1)

    return last_output, outputs, [h_n, c_n]