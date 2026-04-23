def _prepare_reference_model_for_verify(reference_model: nn.Module) -> None:
    # Keep verification deterministic and avoid timm patch-drop index path differences across backbones.
    reference_model.encoder.backbone.patch_drop = nn.Identity()

    original_pos_embed = reference_model.encoder.backbone._pos_embed

    def _safe_pos_embed(x: torch.Tensor):
        # timm EVA `_pos_embed` internally calls `self.patch_drop(x)` and expects `(x, keep_indices)`.
        # Upstream VidEoMT wrapper then calls `patch_drop` once more and expects a tensor.
        # We temporarily disable the internal patch_drop call to avoid API mismatch, while keeping
        # the outer wrapper path deterministic via `nn.Identity`.
        original_patch_drop = reference_model.encoder.backbone.patch_drop
        reference_model.encoder.backbone.patch_drop = None
        pos_embed_output = original_pos_embed(x)
        reference_model.encoder.backbone.patch_drop = original_patch_drop

        # Newer timm EVA backbones may return `(tokens, rope)` while the upstream VidEoMT wrapper
        # expects `_pos_embed` to return only tokens.
        if isinstance(pos_embed_output, tuple):
            return pos_embed_output[0]
        return pos_embed_output

    reference_model.encoder.backbone._pos_embed = _safe_pos_embed

    # timm EVA blocks expose gamma_1/gamma_2, while the VidEoMT wrapper calls ls1/ls2 modules.
    for block in reference_model.encoder.backbone.blocks:
        if not hasattr(block, "ls1") and hasattr(block, "gamma_1"):
            block.ls1 = _ReferenceLayerScaleAdapter(block.gamma_1)
        if not hasattr(block, "ls2") and hasattr(block, "gamma_2"):
            block.ls2 = _ReferenceLayerScaleAdapter(block.gamma_2)

        # Upstream wrapper `_attn` expects timm attention modules to expose `head_dim`.
        if hasattr(block, "attn") and not hasattr(block.attn, "head_dim") and hasattr(block.attn, "qkv"):
            block.attn.head_dim = block.attn.qkv.weight.shape[0] // (3 * block.attn.num_heads)