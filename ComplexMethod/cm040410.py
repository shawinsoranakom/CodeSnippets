def tile(x, repeats):
    x = convert_to_tensor(x)

    # Convert repeats to a list (works for both sequences and 1D tensors)
    if isinstance(repeats, int):
        repeats = [repeats]
    else:
        repeats = [v for v in repeats]

    # Process list elements: convert concrete scalar tensors to Python ints
    processed_repeats = []
    for r in repeats:
        if hasattr(r, "numpy") and r.shape == ():
            processed_repeats.append(int(r.numpy()))
        else:
            processed_repeats.append(r)
    repeats = processed_repeats

    # Get x rank
    x_rank = x.shape.rank

    # Pad repeats if needed
    if len(repeats) < x_rank:
        repeats = [1] * (x_rank - len(repeats)) + repeats

    # Add dimensions to x if needed using tf.expand_dims
    while len(repeats) > x.shape.rank:
        x = tf.expand_dims(x, 0)

    return tf.tile(x, repeats)