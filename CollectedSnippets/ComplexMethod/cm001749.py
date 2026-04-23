def _prepare_for_class(self, inputs_dict, model_class, return_labels=False):
        inputs_dict = copy.deepcopy(inputs_dict)
        if model_class.__name__ in get_values(MODEL_FOR_MULTIPLE_CHOICE_MAPPING_NAMES):
            inputs_dict = {
                k: v.unsqueeze(1).expand(-1, self.model_tester.num_choices, -1).contiguous()
                if isinstance(v, torch.Tensor) and v.ndim > 1
                else v
                for k, v in inputs_dict.items()
            }
        elif model_class.__name__ in get_values(MODEL_FOR_AUDIO_XVECTOR_MAPPING_NAMES):
            inputs_dict.pop("attention_mask", None)
        elif model_class.__name__ == MODEL_FOR_PRETRAINING_MAPPING_NAMES["hiera"]:
            config = self.model_tester.get_config()
            mask_spatial_shape = [
                i // s // ms for i, s, ms in zip(config.image_size, config.patch_stride, config.masked_unit_size)
            ]
            num_windows = math.prod(mask_spatial_shape)
            set_seed(42)
            inputs_dict["noise"] = torch.rand(self.model_tester.batch_size, num_windows)

        if return_labels:
            if model_class.__name__ in get_values(MODEL_FOR_MULTIPLE_CHOICE_MAPPING_NAMES):
                inputs_dict["labels"] = torch.ones(self.model_tester.batch_size, dtype=torch.long, device=torch_device)
            elif model_class.__name__ in [
                *get_values(MODEL_FOR_QUESTION_ANSWERING_MAPPING_NAMES),
                *get_values(MODEL_FOR_DOCUMENT_QUESTION_ANSWERING_MAPPING_NAMES),
            ]:
                inputs_dict["start_positions"] = torch.zeros(
                    self.model_tester.batch_size, dtype=torch.long, device=torch_device
                )
                inputs_dict["end_positions"] = torch.zeros(
                    self.model_tester.batch_size, dtype=torch.long, device=torch_device
                )
            elif model_class.__name__ in [
                *get_values(MODEL_FOR_SEQUENCE_CLASSIFICATION_MAPPING_NAMES),
                *get_values(MODEL_FOR_NEXT_SENTENCE_PREDICTION_MAPPING_NAMES),
                *get_values(MODEL_FOR_IMAGE_CLASSIFICATION_MAPPING_NAMES),
                *get_values(MODEL_FOR_VIDEO_CLASSIFICATION_MAPPING_NAMES),
                *get_values(MODEL_FOR_AUDIO_CLASSIFICATION_MAPPING_NAMES),
            ]:
                inputs_dict["labels"] = torch.zeros(
                    self.model_tester.batch_size, dtype=torch.long, device=torch_device
                )
            elif model_class.__name__ in [
                *get_values(MODEL_FOR_TOKEN_CLASSIFICATION_MAPPING_NAMES),
                *get_values(MODEL_FOR_CAUSAL_LM_MAPPING_NAMES),
                *get_values(MODEL_FOR_CAUSAL_IMAGE_MODELING_MAPPING_NAMES),
                *get_values(MODEL_FOR_IMAGE_TEXT_TO_TEXT_MAPPING_NAMES),
                *get_values(MODEL_FOR_MASKED_LM_MAPPING_NAMES),
                *get_values(MODEL_FOR_SEQ_TO_SEQ_CAUSAL_LM_MAPPING_NAMES),
                *get_values(MODEL_FOR_CTC_MAPPING_NAMES),
            ]:
                inputs_dict["labels"] = torch.zeros(
                    (self.model_tester.batch_size, self.model_tester.seq_length), dtype=torch.long, device=torch_device
                )
            elif model_class.__name__ in get_values(MODEL_FOR_MASKED_IMAGE_MODELING_MAPPING_NAMES):
                num_patches = self.model_tester.image_size // self.model_tester.patch_size
                inputs_dict["bool_masked_pos"] = torch.zeros(
                    (self.model_tester.batch_size, num_patches**2), dtype=torch.long, device=torch_device
                )
            elif model_class.__name__ in get_values(MODEL_FOR_SEMANTIC_SEGMENTATION_MAPPING_NAMES):
                batch_size, num_channels, height, width = inputs_dict["pixel_values"].shape
                inputs_dict["labels"] = torch.zeros(
                    [self.model_tester.batch_size, height, width], device=torch_device
                ).long()

        return inputs_dict