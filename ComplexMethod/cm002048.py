def prepare_config_and_inputs(self, model_class=None):
        config = self.get_config()

        input_mask = None
        sequence_labels = None
        token_labels = None
        if self.use_labels:
            sequence_labels = ids_tensor([self.batch_size], self.num_labels)
            token_labels = ids_tensor([self.batch_size, self.seq_length], self.num_labels)

        if model_class is None or model_class.__name__ == "PerceiverModel":
            inputs = floats_tensor([self.batch_size, self.seq_length, config.d_model], scale=1.0)
            return config, inputs, input_mask, sequence_labels, token_labels
        elif model_class.__name__ in ["PerceiverForMaskedLM", "PerceiverForSequenceClassification"]:
            inputs = ids_tensor([self.batch_size, self.seq_length], self.vocab_size)
            # input mask is only relevant for text inputs
            if self.use_input_mask:
                input_mask = random_attention_mask([self.batch_size, self.seq_length])
        elif model_class.__name__ == "PerceiverForImageClassificationLearned":
            inputs = floats_tensor([self.batch_size, self.num_channels, self.image_size, self.image_size])
        elif model_class.__name__ == "PerceiverForImageClassificationFourier":
            inputs = floats_tensor([self.batch_size, self.num_channels, self.image_size, self.image_size])
        elif model_class.__name__ == "PerceiverForImageClassificationConvProcessing":
            inputs = floats_tensor([self.batch_size, self.num_channels, self.image_size, self.image_size])
        elif model_class.__name__ == "PerceiverForOpticalFlow":
            inputs = floats_tensor([self.batch_size, 2, 27, self.train_size[0], self.train_size[1]])
        elif model_class.__name__ == "PerceiverForMultimodalAutoencoding":
            images = torch.randn(
                (self.batch_size, self.num_frames, self.num_channels, self.image_size, self.image_size),
                device=torch_device,
            )
            audio = torch.randn(
                (self.batch_size, self.num_frames * self.audio_samples_per_frame, 1), device=torch_device
            )
            inputs = {
                "image": images,
                "audio": audio,
                "label": torch.zeros((self.batch_size, self.num_labels), device=torch_device),
            }
        else:
            raise ValueError(f"Model class {model_class} not supported")

        return config, inputs, input_mask, sequence_labels, token_labels