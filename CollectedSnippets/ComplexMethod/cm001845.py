def test_retain_grad_hidden_states_attentions(self):
        config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()
        for k in config.sub_configs:
            if getattr(config, k) is not None:
                getattr(config, k).output_hidden_states = True
                getattr(config, k).output_attentions = True

        config.output_hidden_states = True
        config.output_attentions = True
        config._attn_implementation = "eager"

        # Use first model class
        model_class = self.all_model_classes[0]
        model = model_class._from_config(config, attn_implementation="eager")
        model.to(torch_device)

        inputs = self._prepare_for_class(inputs_dict, model_class)
        outputs = model(**inputs)

        output = outputs[0]

        # SAM3 has component-specific hidden states and attentions
        # Check vision hidden states and attentions
        if outputs.vision_hidden_states is not None and len(outputs.vision_hidden_states) > 0:
            vision_hidden_states = outputs.vision_hidden_states[0]
            vision_hidden_states.retain_grad()

        if outputs.vision_attentions is not None and len(outputs.vision_attentions) > 0:
            vision_attentions = outputs.vision_attentions[0]
            vision_attentions.retain_grad()

        # Check DETR encoder hidden states and attentions
        if outputs.encoder_hidden_states is not None and len(outputs.encoder_hidden_states) > 0:
            encoder_hidden_states = outputs.encoder_hidden_states[0]
            encoder_hidden_states.retain_grad()

        if outputs.detr_encoder_attentions is not None and len(outputs.detr_encoder_attentions) > 0:
            detr_encoder_attentions = outputs.detr_encoder_attentions[0]
            detr_encoder_attentions.retain_grad()

        # Check DETR decoder hidden states and attentions
        if outputs.decoder_hidden_states is not None and len(outputs.decoder_hidden_states) > 0:
            decoder_hidden_states = outputs.decoder_hidden_states[0]
            decoder_hidden_states.retain_grad()

        if outputs.detr_decoder_attentions is not None and len(outputs.detr_decoder_attentions) > 0:
            detr_decoder_attentions = outputs.detr_decoder_attentions[0]
            detr_decoder_attentions.retain_grad()

        # Check mask decoder attentions
        if outputs.mask_decoder_attentions is not None and len(outputs.mask_decoder_attentions) > 0:
            mask_decoder_attentions = outputs.mask_decoder_attentions[0]
            mask_decoder_attentions.retain_grad()

        output.flatten()[0].backward(retain_graph=True)

        # Check gradients are not None
        if outputs.vision_hidden_states is not None and len(outputs.vision_hidden_states) > 0:
            self.assertIsNotNone(vision_hidden_states.grad)

        if outputs.vision_attentions is not None and len(outputs.vision_attentions) > 0:
            self.assertIsNotNone(vision_attentions.grad)

        if outputs.encoder_hidden_states is not None and len(outputs.encoder_hidden_states) > 0:
            self.assertIsNotNone(encoder_hidden_states.grad)

        if outputs.detr_encoder_attentions is not None and len(outputs.detr_encoder_attentions) > 0:
            self.assertIsNotNone(detr_encoder_attentions.grad)

        if outputs.decoder_hidden_states is not None and len(outputs.decoder_hidden_states) > 0:
            self.assertIsNotNone(decoder_hidden_states.grad)

        if outputs.detr_decoder_attentions is not None and len(outputs.detr_decoder_attentions) > 0:
            self.assertIsNotNone(detr_decoder_attentions.grad)

        if outputs.mask_decoder_attentions is not None and len(outputs.mask_decoder_attentions) > 0:
            self.assertIsNotNone(mask_decoder_attentions.grad)