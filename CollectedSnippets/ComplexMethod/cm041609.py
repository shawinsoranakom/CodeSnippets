def test_get_freeze_model_layers(model):
    """Verify layer-wise freezing: only the last layer stays trainable."""
    # Freeze all but last layer
    config = {"name": "freeze", "freeze_trainable_layers": 1, "freeze_trainable_modules": "all"}

    # Ensure we start with something known
    model = peft_module.get_freeze_model(model, config, is_train=True)

    num_layers = model.config.num_hidden_layers
    assert num_layers > 0

    for name, param in model.named_parameters():
        if f"layers.{num_layers - 1}" in name:
            assert param.requires_grad, f"{name} should be trainable"
        elif "layers.0" in name and num_layers > 1:
            assert not param.requires_grad, f"{name} should be frozen"