def load_tf_weights_in_openai_gpt(model, config, openai_checkpoint_folder_path):
    """Load tf pre-trained weights in a pytorch model (from NumPy arrays here)"""
    import re

    import numpy as np

    if ".ckpt" in openai_checkpoint_folder_path:
        openai_checkpoint_folder_path = os.path.dirname(openai_checkpoint_folder_path)

    logger.info(f"Loading weights from {openai_checkpoint_folder_path}")

    with open(openai_checkpoint_folder_path + "/parameters_names.json", "r", encoding="utf-8") as names_handle:
        names = json.load(names_handle)
    with open(openai_checkpoint_folder_path + "/params_shapes.json", "r", encoding="utf-8") as shapes_handle:
        shapes = json.load(shapes_handle)
    offsets = np.cumsum([np.prod(shape) for shape in shapes])
    init_params = [np.load(openai_checkpoint_folder_path + f"/params_{n}.npy") for n in range(10)]
    init_params = np.split(np.concatenate(init_params, 0), offsets)[:-1]
    init_params = [param.reshape(shape) for param, shape in zip(init_params, shapes)]

    # This was used when we had a single embedding matrix for positions and tokens
    # init_params[0] = np.concatenate([init_params[1], init_params[0]], 0)
    # del init_params[1]
    init_params = [arr.squeeze() for arr in init_params]

    # Check that the token and position embeddings weight dimensions map those of the init parameters.
    if model.tokens_embed.weight.shape != init_params[1].shape:
        raise ValueError(
            f"tokens_embed.weight.shape: {model.tokens_embed.weight.shape} does not match init_param[1].shape:"
            f" {init_params[1].shape}"
        )

    if model.positions_embed.weight.shape != init_params[0].shape:
        raise ValueError(
            f"positions_embed.weight.shape: {model.positions_embed.weight.shape} does not match init_param[0].shape:"
            f" {init_params[0].shape}"
        )

    model.tokens_embed.weight.data = torch.from_numpy(init_params[1])
    model.positions_embed.weight.data = torch.from_numpy(init_params[0])
    names.pop(0)
    # Pop position and token embedding arrays
    init_params.pop(0)
    init_params.pop(0)

    for name, array in zip(names, init_params):  # names[1:n_transfer], init_params[1:n_transfer]):
        name = name[6:]  # skip "model/"
        if name[-2:] != ":0":
            raise ValueError(f"Layer {name} does not end with :0")
        name = name[:-2]
        name = name.split("/")
        pointer = model
        for m_name in name:
            if re.fullmatch(r"[A-Za-z]+\d+", m_name):
                scope_names = re.split(r"(\d+)", m_name)
            else:
                scope_names = [m_name]
            if scope_names[0] == "g":
                pointer = getattr(pointer, "weight")
            elif scope_names[0] == "b":
                pointer = getattr(pointer, "bias")
            elif scope_names[0] == "w":
                pointer = getattr(pointer, "weight")
            else:
                pointer = getattr(pointer, scope_names[0])
            if len(scope_names) >= 2:
                num = int(scope_names[1])
                pointer = pointer[num]

        # Ensure that the pointer and array have compatible shapes.
        if pointer.shape != array.shape:
            raise ValueError(f"Pointer shape {pointer.shape} and array shape {array.shape} mismatched")

        logger.info(f"Initialize PyTorch weight {name}")
        pointer.data = torch.from_numpy(array)
    return model