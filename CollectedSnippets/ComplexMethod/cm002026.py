def test_attention_outputs(self):
        if not self.has_attentions:
            self.skipTest(reason="has_attentions is set to False")

        else:
            config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()
            config.return_dict = True

            seq_len = getattr(self.model_tester, "seq_length", None)
            decoder_seq_length = getattr(self.model_tester, "decoder_seq_length", seq_len)
            encoder_seq_length = getattr(self.model_tester, "encoder_seq_length", seq_len)
            decoder_key_length = getattr(self.model_tester, "decoder_key_length", decoder_seq_length)
            encoder_key_length = getattr(self.model_tester, "key_length", encoder_seq_length)
            chunk_length = getattr(self.model_tester, "chunk_length", None)
            block_len = getattr(self.model_tester, "block_len", None)
            global_block_size = getattr(self.model_tester, "global_block_size", None)
            global_seq_len = encoder_seq_length // global_block_size

            if chunk_length is not None and hasattr(self.model_tester, "num_hashes"):
                encoder_seq_length = encoder_seq_length * self.model_tester.num_hashes

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
                    [self.model_tester.num_attention_heads, block_len, 3 * block_len + global_seq_len],
                )
                out_len = len(outputs)

                if self.is_encoder_decoder:
                    correct_outlen = 5

                    # loss is at first position
                    if "labels" in inputs_dict:
                        correct_outlen += 1  # loss is added to beginning
                    # Question Answering model returns start_logits and end_logits
                    if model_class in get_values(MODEL_FOR_QUESTION_ANSWERING_MAPPING):
                        correct_outlen += 1  # start_logits and end_logits instead of only 1 output
                    if "past_key_values" in outputs:
                        correct_outlen += 1  # past_key_values have been returned

                    self.assertEqual(out_len, correct_outlen)

                    # decoder attentions
                    decoder_attentions = outputs.decoder_attentions
                    self.assertIsInstance(decoder_attentions, (list, tuple))
                    self.assertEqual(len(decoder_attentions), self.model_tester.num_hidden_layers)
                    self.assertListEqual(
                        list(decoder_attentions[0].shape[-3:]),
                        [self.model_tester.num_attention_heads, decoder_seq_length, decoder_key_length],
                    )

                    # cross attentions
                    cross_attentions = outputs.cross_attentions
                    self.assertIsInstance(cross_attentions, (list, tuple))
                    self.assertEqual(len(cross_attentions), self.model_tester.num_hidden_layers)
                    self.assertListEqual(
                        list(cross_attentions[0].shape[-3:]),
                        [
                            self.model_tester.num_attention_heads,
                            decoder_seq_length,
                            encoder_key_length,
                        ],
                    )

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
                    [self.model_tester.num_attention_heads, block_len, 3 * block_len + global_seq_len],
                )