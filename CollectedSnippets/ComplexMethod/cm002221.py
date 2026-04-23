def sparse_model_config(model_config):
    embedding_size = None
    if hasattr(model_config, "hidden_size"):
        embedding_size = model_config.hidden_size
    elif hasattr(model_config, "n_embed"):
        embedding_size = model_config.n_embed
    elif hasattr(model_config, "n_embd"):
        embedding_size = model_config.n_embd

    num_head = None
    if hasattr(model_config, "num_attention_heads"):
        num_head = model_config.num_attention_heads
    elif hasattr(model_config, "n_head"):
        num_head = model_config.n_head

    if embedding_size is None or num_head is None or num_head == 0:
        raise ValueError("Check the model config")

    num_embedding_size_per_head = int(embedding_size / num_head)
    if hasattr(model_config, "n_layer"):
        num_layer = model_config.n_layer
    elif hasattr(model_config, "num_hidden_layers"):
        num_layer = model_config.num_hidden_layers
    else:
        raise ValueError("Number of hidden layers couldn't be determined from the model config")

    return num_layer, num_head, num_embedding_size_per_head