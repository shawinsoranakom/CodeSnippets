def _get_model_size(model):
    model_size = 0
    for name, child in model.named_children():
        if not isinstance(child, torch.nn.Embedding):
            model_size += sum(
                p.numel() * p.dtype.itemsize
                for p in itertools.chain(child.parameters(), child.buffers())
            )

    # Remove the inactivated experts from the model size if this is mixture of experts
    # architecture, since only activated experts are loaded.
    if hasattr(model.config, "num_experts"):
        config = model.config
        for submodule in model.modules():
            if isinstance(
                submodule, (ConditionalFeedForward, ConditionalFeedForwardInt8)
            ):
                model_size -= (
                    sum(
                        p.numel() * p.dtype.itemsize
                        for p in itertools.chain(
                            submodule.parameters(), child.buffers()
                        )
                    )
                    * (config.num_experts - config.num_activated_experts)
                    / config.num_experts
                )

    return model_size