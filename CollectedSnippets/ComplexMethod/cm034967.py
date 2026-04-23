def _init_weights(module: nn.Layer, name: str = "", zero_init_last=True):
    if isinstance(module, nn.Linear) or (
        "head.fc" in name and isinstance(module, nn.Conv2D)
    ):
        normal_(module.weight)
        zeros_(module.bias)
    elif isinstance(module, nn.Conv2D):
        kaiming_normal_(module.weight)
        if module.bias is not None:
            zeros_(module.bias)
    elif isinstance(module, (nn.BatchNorm2D, nn.LayerNorm, nn.GroupNorm)):
        ones_(module.weight)
        zeros_(module.bias)
    elif zero_init_last and hasattr(module, "zero_init_last"):
        module.zero_init_last()