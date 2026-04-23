def prepare_config_and_inputs(self):
        input_ids = ids_tensor([self.batch_size, self.seq_length], self.vocab_size)

        bbox = ids_tensor([self.batch_size, self.seq_length, 4], self.range_bbox)
        # Ensure that bbox is legal
        for i in range(bbox.shape[0]):
            for j in range(bbox.shape[1]):
                if bbox[i, j, 3] < bbox[i, j, 1]:
                    t = bbox[i, j, 3]
                    bbox[i, j, 3] = bbox[i, j, 1]
                    bbox[i, j, 1] = t
                if bbox[i, j, 2] < bbox[i, j, 0]:
                    t = bbox[i, j, 2]
                    bbox[i, j, 2] = bbox[i, j, 0]
                    bbox[i, j, 0] = t

        image = ImageList(
            torch.zeros(self.batch_size, self.num_channels, self.image_size, self.image_size, device=torch_device),
            self.image_size,
        )

        input_mask = None
        if self.use_input_mask:
            input_mask = random_attention_mask([self.batch_size, self.seq_length])

        token_type_ids = None
        if self.use_token_type_ids:
            token_type_ids = ids_tensor([self.batch_size, self.seq_length], self.type_vocab_size)

        sequence_labels = None
        token_labels = None
        if self.use_labels:
            sequence_labels = ids_tensor([self.batch_size], self.type_sequence_label_size)
            token_labels = ids_tensor([self.batch_size, self.seq_length], self.num_labels)

        config = LayoutLMv2Config(
            vocab_size=self.vocab_size,
            hidden_size=self.hidden_size,
            num_hidden_layers=self.num_hidden_layers,
            num_attention_heads=self.num_attention_heads,
            intermediate_size=self.intermediate_size,
            hidden_act=self.hidden_act,
            hidden_dropout_prob=self.hidden_dropout_prob,
            attention_probs_dropout_prob=self.attention_probs_dropout_prob,
            max_position_embeddings=self.max_position_embeddings,
            type_vocab_size=self.type_vocab_size,
            is_decoder=False,
            initializer_range=self.initializer_range,
            image_feature_pool_shape=self.image_feature_pool_shape,
            coordinate_size=self.coordinate_size,
            shape_size=self.shape_size,
            detectron2_config_args=self.detectron2_config,
        )

        return config, input_ids, bbox, image, token_type_ids, input_mask, sequence_labels, token_labels