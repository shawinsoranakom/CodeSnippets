def _assert_fake_quantizers_are_called(model: torch.nn.Module):
        for name, child in model.named_children():
            if full_finetuning:
                if isinstance(child, FakeQuantizedLinear):
                    if not weight_only:
                        assert child.activation_fake_quantizer.count == 1
                    assert child.weight_fake_quantizer.count == 1
            else:
                # For LoRA, we only fake quantize the input activations once per block:
                # For self_attn, we only fake quantize the q_proj's input activations
                # For mlp, we only fake quantize the gate_proj's input activations
                if name == "self_attn":
                    base_layer = child.q_proj.base_layer
                    if not weight_only:
                        assert hasattr(base_layer, "activation_fake_quantizer")
                        assert base_layer.activation_fake_quantizer.count == 1
                elif name == "mlp":
                    base_layer = child.gate_proj.base_layer
                    if not weight_only:
                        assert hasattr(base_layer, "activation_fake_quantizer")
                        assert base_layer.activation_fake_quantizer.count == 1
                elif isinstance(child, FakeQuantizedLinear):
                    # Weight fake quantizers should always be called
                    assert child.weight_fake_quantizer.count == 1