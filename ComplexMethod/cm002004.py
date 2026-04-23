def _prepare_for_class(self, inputs_dict, model_class, return_labels=False):
        inputs_dict = copy.deepcopy(inputs_dict)
        if model_class == VisualBertForMultipleChoice:
            for key in inputs_dict:
                value = inputs_dict[key]
                if isinstance(value, torch.Tensor) and value.ndim > 1:
                    if key != "visual_embeds":
                        inputs_dict[key] = (
                            inputs_dict[key].unsqueeze(1).expand(-1, self.model_tester.num_choices, -1).contiguous()
                        )
                    else:
                        inputs_dict[key] = (
                            inputs_dict[key]
                            .unsqueeze(1)
                            .expand(-1, self.model_tester.num_choices, -1, self.model_tester.visual_embedding_dim)
                            .contiguous()
                        )

        elif model_class == VisualBertForRegionToPhraseAlignment:
            total_length = self.model_tester.seq_length + self.model_tester.visual_seq_length
            batch_size = self.model_tester.batch_size
            inputs_dict["region_to_phrase_position"] = torch.zeros(
                (batch_size, total_length),
                dtype=torch.long,
                device=torch_device,
            )

        if return_labels:
            if model_class == VisualBertForMultipleChoice:
                inputs_dict["labels"] = torch.zeros(
                    self.model_tester.batch_size, dtype=torch.long, device=torch_device
                )
            elif model_class == VisualBertForPreTraining:
                total_length = self.model_tester.seq_length + self.model_tester.visual_seq_length
                batch_size = self.model_tester.batch_size
                inputs_dict["labels"] = torch.zeros(
                    (batch_size, total_length),
                    dtype=torch.long,
                    device=torch_device,
                )
                inputs_dict["sentence_image_labels"] = torch.zeros(
                    self.model_tester.batch_size, dtype=torch.long, device=torch_device
                )

            # Flickr expects float labels
            elif model_class == VisualBertForRegionToPhraseAlignment:
                batch_size = self.model_tester.batch_size
                total_length = self.model_tester.seq_length + self.model_tester.visual_seq_length

                inputs_dict["labels"] = torch.ones(
                    (
                        batch_size,
                        total_length,
                        self.model_tester.visual_seq_length,
                    ),
                    dtype=torch.float,
                    device=torch_device,
                )

            # VQA expects float labels
            elif model_class == VisualBertForQuestionAnswering:
                inputs_dict["labels"] = torch.ones(
                    (self.model_tester.batch_size, self.model_tester.num_labels),
                    dtype=torch.float,
                    device=torch_device,
                )

            elif model_class == VisualBertForVisualReasoning:
                inputs_dict["labels"] = torch.zeros(
                    (self.model_tester.batch_size), dtype=torch.long, device=torch_device
                )

        return inputs_dict