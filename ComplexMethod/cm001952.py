def _prepare_for_class(self, inputs_dict, model_class, return_labels=False):
        inputs_dict = copy.deepcopy(inputs_dict)
        if model_class in get_values(MODEL_FOR_MULTIPLE_CHOICE_MAPPING):
            inputs_dict = {
                k: v.unsqueeze(1).expand(-1, self.model_tester.num_choices, -1).contiguous()
                if isinstance(v, torch.Tensor) and v.ndim > 1
                else v
                for k, v in inputs_dict.items()
            }

        if return_labels:
            if model_class in get_values(MODEL_FOR_MULTIPLE_CHOICE_MAPPING):
                inputs_dict["labels"] = torch.ones(self.model_tester.batch_size, dtype=torch.long, device=torch_device)
            elif model_class in get_values(MODEL_FOR_TABLE_QUESTION_ANSWERING_MAPPING):
                inputs_dict["labels"] = torch.zeros(
                    (self.model_tester.batch_size, self.model_tester.seq_length), dtype=torch.long, device=torch_device
                )
                inputs_dict["aggregation_labels"] = torch.zeros(
                    self.model_tester.batch_size, dtype=torch.long, device=torch_device
                )
                inputs_dict["numeric_values"] = torch.zeros(
                    (self.model_tester.batch_size, self.model_tester.seq_length),
                    dtype=torch.float,
                    device=torch_device,
                )
                inputs_dict["numeric_values_scale"] = torch.zeros(
                    (self.model_tester.batch_size, self.model_tester.seq_length),
                    dtype=torch.float,
                    device=torch_device,
                )
                inputs_dict["float_answer"] = torch.zeros(
                    self.model_tester.batch_size, dtype=torch.float, device=torch_device
                )
            elif model_class in [
                *get_values(MODEL_FOR_SEQUENCE_CLASSIFICATION_MAPPING),
                *get_values(MODEL_FOR_NEXT_SENTENCE_PREDICTION_MAPPING),
            ]:
                inputs_dict["labels"] = torch.zeros(
                    self.model_tester.batch_size, dtype=torch.long, device=torch_device
                )
            elif model_class in [
                *get_values(MODEL_FOR_TOKEN_CLASSIFICATION_MAPPING),
                *get_values(MODEL_FOR_CAUSAL_LM_MAPPING),
                *get_values(MODEL_FOR_MASKED_LM_MAPPING),
                *get_values(MODEL_FOR_SEQ_TO_SEQ_CAUSAL_LM_MAPPING),
            ]:
                inputs_dict["labels"] = torch.zeros(
                    (self.model_tester.batch_size, self.model_tester.seq_length), dtype=torch.long, device=torch_device
                )
        return inputs_dict