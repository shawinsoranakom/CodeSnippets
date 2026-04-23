def test_attention_outputs(self):
        config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()
        config.return_dict = True

        seq_len = getattr(self.model_tester, "seq_length", None)
        decoder_seq_length = getattr(self.model_tester, "decoder_seq_length", seq_len)
        encoder_seq_length = getattr(self.model_tester, "encoder_seq_length", seq_len)
        d_model = getattr(self.model_tester, "d_model", None)
        num_attention_heads = getattr(self.model_tester, "num_attention_heads", None)
        dim = d_model // num_attention_heads

        for model_class in self.all_model_classes:
            inputs_dict["output_attentions"] = True
            inputs_dict["output_hidden_states"] = False
            config.return_dict = True
            model = model_class._from_config(config, attn_implementation="eager")
            config = model.config
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
            attentions = outputs.encoder_attentions
            self.assertEqual(len(attentions), self.model_tester.num_hidden_layers)

            self.assertListEqual(
                list(attentions[0].shape[-3:]),
                [self.model_tester.num_attention_heads, encoder_seq_length, dim],
            )
            out_len = len(outputs)

            correct_outlen = 7

            if "last_hidden_state" in outputs:
                correct_outlen += 1

            if "trend" in outputs:
                correct_outlen += 1

            if "past_key_values" in outputs:
                correct_outlen += 1  # past_key_values have been returned

            if "loss" in outputs:
                correct_outlen += 1

            if "params" in outputs:
                correct_outlen += 1

            self.assertEqual(out_len, correct_outlen)

            # decoder attentions
            decoder_attentions = outputs.decoder_attentions
            self.assertIsInstance(decoder_attentions, (list, tuple))
            self.assertEqual(len(decoder_attentions), self.model_tester.num_hidden_layers)
            self.assertListEqual(
                list(decoder_attentions[0].shape[-3:]),
                [self.model_tester.num_attention_heads, decoder_seq_length, dim],
            )

            # cross attentions
            cross_attentions = outputs.cross_attentions
            self.assertIsInstance(cross_attentions, (list, tuple))
            self.assertEqual(len(cross_attentions), self.model_tester.num_hidden_layers)
            self.assertListEqual(
                list(cross_attentions[0].shape[-3:]),
                [self.model_tester.num_attention_heads, decoder_seq_length, dim],
            )

        # Check attention is always last and order is fine
        inputs_dict["output_attentions"] = True
        inputs_dict["output_hidden_states"] = True
        model = model_class(config)
        model.to(torch_device)
        model.eval()
        with torch.no_grad():
            outputs = model(**self._prepare_for_class(inputs_dict, model_class))

        self.assertEqual(out_len + 2, len(outputs))

        self_attentions = outputs.encoder_attentions if config.is_encoder_decoder else outputs.attentions

        self.assertEqual(len(self_attentions), self.model_tester.num_hidden_layers)
        self.assertListEqual(
            list(self_attentions[0].shape[-3:]),
            [self.model_tester.num_attention_heads, encoder_seq_length, dim],
        )