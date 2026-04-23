def _get_train_sampler(self, train_dataset: Dataset | None = None) -> torch.utils.data.Sampler | None:
        """Return the training sampler based on `train_sampling_strategy`."""
        if train_dataset is None:
            train_dataset = self.train_dataset
        if train_dataset is None or not has_length(train_dataset):
            return None

        # Build the sampler.
        if self.args.train_sampling_strategy == "group_by_length":
            if is_datasets_available() and isinstance(train_dataset, datasets.Dataset):
                lengths = (
                    train_dataset[self.args.length_column_name]
                    if self.args.length_column_name in train_dataset.column_names
                    else None
                )
            else:
                lengths = None
            model_input_name = (
                self.processing_class.model_input_names[0] if self.processing_class is not None else None
            )
            return LengthGroupedSampler(
                self.args.train_batch_size * self.args.gradient_accumulation_steps,
                dataset=train_dataset,
                lengths=lengths,
                model_input_name=model_input_name,
            )
        elif self.args.train_sampling_strategy == "sequential":
            return SequentialSampler(train_dataset)
        else:
            return RandomSampler(train_dataset)