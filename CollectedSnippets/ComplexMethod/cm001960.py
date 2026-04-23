def _prepare_for_class(self, inputs_dict, model_class, return_labels=False):
        entity_inputs_dict = {k: v for k, v in inputs_dict.items() if k.startswith("entity")}
        inputs_dict = {k: v for k, v in inputs_dict.items() if not k.startswith("entity")}

        inputs_dict = super()._prepare_for_class(inputs_dict, model_class, return_labels=return_labels)
        if model_class == LukeForMultipleChoice:
            entity_inputs_dict = {
                k: v.unsqueeze(1).expand(-1, self.model_tester.num_choices, -1).contiguous()
                if v.ndim == 2
                else v.unsqueeze(1).expand(-1, self.model_tester.num_choices, -1, -1).contiguous()
                for k, v in entity_inputs_dict.items()
            }
        inputs_dict.update(entity_inputs_dict)

        if model_class == LukeForEntitySpanClassification:
            inputs_dict["entity_start_positions"] = torch.zeros(
                (self.model_tester.batch_size, self.model_tester.entity_length), dtype=torch.long, device=torch_device
            )
            inputs_dict["entity_end_positions"] = torch.ones(
                (self.model_tester.batch_size, self.model_tester.entity_length), dtype=torch.long, device=torch_device
            )

        if return_labels:
            if model_class in (
                LukeForEntityClassification,
                LukeForEntityPairClassification,
                LukeForSequenceClassification,
                LukeForMultipleChoice,
            ):
                inputs_dict["labels"] = torch.zeros(
                    self.model_tester.batch_size, dtype=torch.long, device=torch_device
                )
            elif model_class == LukeForEntitySpanClassification:
                inputs_dict["labels"] = torch.zeros(
                    (self.model_tester.batch_size, self.model_tester.entity_length),
                    dtype=torch.long,
                    device=torch_device,
                )
            elif model_class == LukeForTokenClassification:
                inputs_dict["labels"] = torch.zeros(
                    (self.model_tester.batch_size, self.model_tester.seq_length),
                    dtype=torch.long,
                    device=torch_device,
                )
            elif model_class == LukeForMaskedLM:
                inputs_dict["labels"] = torch.zeros(
                    (self.model_tester.batch_size, self.model_tester.seq_length),
                    dtype=torch.long,
                    device=torch_device,
                )
                inputs_dict["entity_labels"] = torch.zeros(
                    (self.model_tester.batch_size, self.model_tester.entity_length),
                    dtype=torch.long,
                    device=torch_device,
                )

        return inputs_dict