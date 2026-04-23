def _init_vit_weights(
    module: nn.Layer, name: str = "", head_bias: float = 0.0, jax_impl: bool = False
):
    """ViT weight initialization
    * When called without n, head_bias, jax_impl args it will behave exactly the same
      as my original init for compatibility with prev hparam / downstream use cases (ie DeiT).
    * When called w/ valid n (module name) and jax_impl=True, will (hopefully) match JAX impl
    """
    if isinstance(module, nn.Linear):
        if name.startswith("head"):
            zeros_(module.weight)
            constant_ = Constant(value=head_bias)
            constant_(module.bias, head_bias)
        elif name.startswith("pre_logits"):
            zeros_(module.bias)
        else:
            if jax_impl:
                xavier_uniform_(module.weight)
                if module.bias is not None:
                    if "mlp" in name:
                        normal_(module.bias)
                    else:
                        zeros_(module.bias)
            else:
                trunc_normal_(module.weight)
                if module.bias is not None:
                    zeros_(module.bias)
    elif jax_impl and isinstance(module, nn.Conv2D):
        # NOTE conv was left to pytorch default in my original init
        if module.bias is not None:
            zeros_(module.bias)
    elif isinstance(module, (nn.LayerNorm, nn.GroupNorm, nn.BatchNorm2D)):
        zeros_(module.bias)
        ones_(module.weight)