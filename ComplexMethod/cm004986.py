def load_tf_weights_in_imagegpt(model, config, imagegpt_checkpoint_path):
    """
    Load tf checkpoints in a pytorch model
    """
    try:
        import re

        import tensorflow as tf
    except ImportError:
        logger.error(
            "Loading a TensorFlow model in PyTorch, requires TensorFlow to be installed. Please see "
            "https://www.tensorflow.org/install/ for installation instructions."
        )
        raise
    tf_path = os.path.abspath(imagegpt_checkpoint_path)
    logger.info(f"Converting TensorFlow checkpoint from {tf_path}")
    # Load weights from TF model
    init_vars = tf.train.list_variables(tf_path)
    names = []
    arrays = []

    for name, shape in init_vars:
        logger.info(f"Loading TF weight {name} with shape {shape}")
        array = tf.train.load_variable(tf_path, name)
        names.append(name)
        arrays.append(array.squeeze())

    for name, array in zip(names, arrays):
        name = name[6:]  # skip "model/"
        name = name.split("/")

        # adam_v and adam_m are variables used in AdamWeightDecayOptimizer to calculated m and v
        # which are not required for using pretrained model
        if (
            any(
                n in ["adam_v", "adam_m", "AdamWeightDecayOptimizer", "AdamWeightDecayOptimizer_1", "global_step"]
                for n in name
            )
            or name[-1] == "_step"
        ):
            logger.info(f"Skipping {'/'.join(name)}")
            continue

        pointer = model
        if name[-1] != "wtet":
            pointer = getattr(pointer, "transformer")

        for m_name in name:
            if re.fullmatch(r"[A-Za-z]+\d+", m_name):
                scope_names = re.split(r"(\d+)", m_name)
            else:
                scope_names = [m_name]

            if scope_names[0] == "w" or scope_names[0] == "g":
                pointer = getattr(pointer, "weight")
            elif scope_names[0] == "b":
                pointer = getattr(pointer, "bias")
            elif scope_names[0] == "wpe" or scope_names[0] == "wte":
                pointer = getattr(pointer, scope_names[0])
                pointer = getattr(pointer, "weight")
            elif scope_names[0] in ["q_proj", "k_proj", "v_proj"]:
                pointer = getattr(pointer, "c_attn")
                pointer = getattr(pointer, "weight")
            elif len(name) == 3 and name[1] == "attn" and scope_names[0] == "c_proj":
                pointer = getattr(pointer, scope_names[0])
                pointer = getattr(pointer, "weight")
            elif scope_names[0] == "wtet":
                pointer = getattr(pointer, "lm_head")
                pointer = getattr(pointer, "weight")
            elif scope_names[0] == "sos":
                pointer = getattr(pointer, "wte")
                pointer = getattr(pointer, "weight")
            else:
                pointer = getattr(pointer, scope_names[0])
            if len(scope_names) >= 2:
                num = int(scope_names[1])
                pointer = pointer[num]

        if len(name) > 1 and name[1] == "attn" or name[-1] == "wtet" or name[-1] == "sos" or name[-1] == "wte":
            pass  # array is used to initialize only part of the pointer so sizes won't match
        else:
            try:
                assert pointer.shape == array.shape
            except AssertionError as e:
                e.args += (pointer.shape, array.shape)
                raise

        logger.info(f"Initialize PyTorch weight {name}")

        if name[-1] == "q_proj":
            pointer.data[:, : config.n_embd] = torch.from_numpy(array.reshape(config.n_embd, config.n_embd)).T
        elif name[-1] == "k_proj":
            pointer.data[:, config.n_embd : 2 * config.n_embd] = torch.from_numpy(
                array.reshape(config.n_embd, config.n_embd)
            ).T
        elif name[-1] == "v_proj":
            pointer.data[:, 2 * config.n_embd :] = torch.from_numpy(array.reshape(config.n_embd, config.n_embd)).T
        elif len(name) == 3 and name[1] == "attn" and name[2] == "c_proj":
            pointer.data = torch.from_numpy(array.reshape(config.n_embd, config.n_embd))
        elif name[-1] == "wtet":
            pointer.data = torch.from_numpy(array)
        elif name[-1] == "wte":
            pointer.data[: config.vocab_size - 1, :] = torch.from_numpy(array)
        elif name[-1] == "sos":
            pointer.data[-1] = torch.from_numpy(array)
        else:
            pointer.data = torch.from_numpy(array)

    return model