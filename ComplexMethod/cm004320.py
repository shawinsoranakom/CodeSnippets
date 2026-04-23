def load_tf_weights_in_tapas(model, config, tf_checkpoint_path):
    """
    Load tf checkpoints in a PyTorch model. This is an adaptation from load_tf_weights_in_bert

    - add cell selection and aggregation heads
    - take into account additional token type embedding layers
    """
    try:
        import re

        import numpy as np
        import tensorflow as tf
    except ImportError:
        logger.error(
            "Loading a TensorFlow model in PyTorch, requires TensorFlow to be installed. Please see "
            "https://www.tensorflow.org/install/ for installation instructions."
        )
        raise
    tf_path = os.path.abspath(tf_checkpoint_path)
    logger.info(f"Converting TensorFlow checkpoint from {tf_path}")
    # Load weights from TF model
    init_vars = tf.train.list_variables(tf_path)
    names = []
    arrays = []
    for name, shape in init_vars:
        logger.info(f"Loading TF weight {name} with shape {shape}")
        array = tf.train.load_variable(tf_path, name)
        names.append(name)
        arrays.append(array)

    for name, array in zip(names, arrays):
        name = name.split("/")
        # adam_v and adam_m are variables used in AdamWeightDecayOptimizer to calculate m and v
        # which are not required for using pretrained model
        if any(
            n
            in [
                "adam_v",
                "adam_m",
                "AdamWeightDecayOptimizer",
                "AdamWeightDecayOptimizer_1",
                "global_step",
                "seq_relationship",
            ]
            for n in name
        ):
            logger.info(f"Skipping {'/'.join(name)}")
            continue
        # in case the model is TapasForSequenceClassification, we skip output_bias and output_weights
        # since these are not used for classification
        if isinstance(model, TapasForSequenceClassification):
            if any(n in ["output_bias", "output_weights"] for n in name):
                logger.info(f"Skipping {'/'.join(name)}")
                continue
        # in case the model is TapasModel, we skip output_bias, output_weights, output_bias_cls and output_weights_cls
        # since this model does not have MLM and NSP heads
        if isinstance(model, TapasModel):
            if any(n in ["output_bias", "output_weights", "output_bias_cls", "output_weights_cls"] for n in name):
                logger.info(f"Skipping {'/'.join(name)}")
                continue
        # in case the model is TapasForMaskedLM, we skip the pooler
        if isinstance(model, TapasForMaskedLM):
            if any(n == "pooler" for n in name):
                logger.info(f"Skipping {'/'.join(name)}")
                continue
        # if first scope name starts with "bert", change it to "tapas"
        if name[0] == "bert":
            name[0] = "tapas"
        pointer = model
        for m_name in name:
            if re.fullmatch(r"[A-Za-z]+_\d+", m_name):
                scope_names = re.split(r"_(\d+)", m_name)
            else:
                scope_names = [m_name]
            if scope_names[0] == "kernel" or scope_names[0] == "gamma":
                pointer = getattr(pointer, "weight")
            elif scope_names[0] == "beta":
                pointer = getattr(pointer, "bias")
            # cell selection heads
            elif scope_names[0] == "output_bias":
                if not isinstance(model, TapasForMaskedLM):
                    pointer = getattr(pointer, "output_bias")
                else:
                    pointer = getattr(pointer, "bias")
            elif scope_names[0] == "output_weights":
                pointer = getattr(pointer, "output_weights")
            elif scope_names[0] == "column_output_bias":
                pointer = getattr(pointer, "column_output_bias")
            elif scope_names[0] == "column_output_weights":
                pointer = getattr(pointer, "column_output_weights")
            # aggregation head
            elif scope_names[0] == "output_bias_agg":
                pointer = getattr(pointer, "aggregation_classifier")
                pointer = getattr(pointer, "bias")
            elif scope_names[0] == "output_weights_agg":
                pointer = getattr(pointer, "aggregation_classifier")
                pointer = getattr(pointer, "weight")
            # classification head
            elif scope_names[0] == "output_bias_cls":
                pointer = getattr(pointer, "classifier")
                pointer = getattr(pointer, "bias")
            elif scope_names[0] == "output_weights_cls":
                pointer = getattr(pointer, "classifier")
                pointer = getattr(pointer, "weight")
            else:
                try:
                    pointer = getattr(pointer, scope_names[0])
                except AttributeError:
                    logger.info(f"Skipping {'/'.join(name)}")
                    continue
            if len(scope_names) >= 2:
                num = int(scope_names[1])
                pointer = pointer[num]
        if m_name[-11:] == "_embeddings":
            pointer = getattr(pointer, "weight")
        elif m_name[-13:] in [f"_embeddings_{i}" for i in range(7)]:
            pointer = getattr(pointer, "weight")
        elif m_name == "kernel":
            array = np.transpose(array)
        try:
            if pointer.shape != array.shape:
                raise ValueError(f"Pointer shape {pointer.shape} and array shape {array.shape} mismatched")
        except AssertionError as e:
            e.args += (pointer.shape, array.shape)
            raise
        logger.info(f"Initialize PyTorch weight {name}")
        # Added a check to see whether the array is a scalar (because bias terms in Tapas checkpoints can be
        # scalar => should first be converted to numpy arrays)
        if np.isscalar(array):
            array = np.array(array)
        pointer.data = torch.from_numpy(array)
    return model