def test_attention_outputs(self):
        if not self.has_attentions:
            self.skipTest(reason="has_attentions is set to False")

        else:
            config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()
            config.return_dict = True

            block_len = getattr(self.model_tester, "block_len", 4)

            for model_class in self.all_model_classes:
                inputs_dict["output_attentions"] = True
                inputs_dict["output_hidden_states"] = False
                config.return_dict = True
                model = model_class(config)
                model.to(torch_device)
                model.eval()
                with torch.no_grad():
                    outputs = model(**self._prepare_for_class(inputs_dict, model_class))
                attentions = outputs.encoder_attentions if config.is_encoder_decoder else outputs.attentions
                self.assertEqual(len(attentions), self.model_tester.num_hidden_layers)

                # check that output_attentions also work using config
                del inputs_dict["output_attentions"]
                config.output_attentions = True
                model = model_class(config)
                model.to(torch_device)
                model.eval()
                with torch.no_grad():
                    outputs = model(**self._prepare_for_class(inputs_dict, model_class))
                attentions = outputs.encoder_attentions if config.is_encoder_decoder else outputs.attentions
                self.assertEqual(len(attentions), self.model_tester.num_hidden_layers)

                self.assertListEqual(
                    list(attentions[0].shape[-3:]),
                    [self.model_tester.num_attention_heads, block_len, 3 * block_len],
                )
                out_len = len(outputs)

                # Check attention is always last and order is fine
                inputs_dict["output_attentions"] = True
                inputs_dict["output_hidden_states"] = True
                model = model_class(config)
                model.to(torch_device)
                model.eval()
                with torch.no_grad():
                    outputs = model(**self._prepare_for_class(inputs_dict, model_class))

                if hasattr(self.model_tester, "num_hidden_states_types"):
                    added_hidden_states = self.model_tester.num_hidden_states_types
                elif self.is_encoder_decoder:
                    added_hidden_states = 2
                else:
                    added_hidden_states = 1
                self.assertEqual(out_len + added_hidden_states, len(outputs))

                self_attentions = outputs.encoder_attentions if config.is_encoder_decoder else outputs.attentions

                self.assertEqual(len(self_attentions), self.model_tester.num_hidden_layers)
                self.assertListEqual(
                    list(self_attentions[0].shape[-3:]),
                    [self.model_tester.num_attention_heads, block_len, 3 * block_len],
                )