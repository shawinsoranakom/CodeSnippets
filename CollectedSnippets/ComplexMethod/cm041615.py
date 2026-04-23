def test_freeze_train_extra_modules():
    model = load_train_model(freeze_trainable_layers=1, freeze_extra_modules="embed_tokens,lm_head", **TRAIN_ARGS)
    for name, param in model.named_parameters():
        if name.startswith("model.layers.1.") or any(module in name for module in ["embed_tokens", "lm_head"]):
            assert param.requires_grad is True
            assert param.dtype == torch.float32
        else:
            assert param.requires_grad is False
            assert param.dtype == torch.float16