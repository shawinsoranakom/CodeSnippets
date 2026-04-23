def test_router_logits_and_no_aux_loss(self):
        """HYV3 returns router_logits but does not compute aux_loss (always None)."""
        config, input_dict = self.model_tester.prepare_config_and_inputs_for_common()
        config.output_router_logits = True

        for model_class in self.all_model_classes:
            model = model_class(config).to(torch_device).eval()
            with torch.no_grad():
                result = model(**input_dict)

            if hasattr(result, "router_logits") and result.router_logits is not None:
                num_moe_layers = sum(1 for t in config.mlp_layer_types if t == "sparse")
                self.assertEqual(len(result.router_logits), num_moe_layers)
                for rl in result.router_logits:
                    self.assertEqual(rl.shape[-1], config.num_experts)

            if hasattr(result, "aux_loss"):
                self.assertIsNone(result.aux_loss)