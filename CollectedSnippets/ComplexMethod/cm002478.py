def _get_eval_sampler(self, eval_dataset: Dataset) -> torch.utils.data.Sampler | None:
        """Return the evaluation sampler, using sequential ordering when not distributed."""
        if eval_dataset is None or not has_length(eval_dataset):
            return None

        if self.args.train_sampling_strategy == "group_by_length":
            if is_datasets_available() and isinstance(eval_dataset, datasets.Dataset):
                lengths = (
                    eval_dataset[self.args.length_column_name]
                    if self.args.length_column_name in eval_dataset.column_names
                    else None
                )
            else:
                lengths = None
            model_input_name = (
                self.processing_class.model_input_names[0] if self.processing_class is not None else None
            )
            return LengthGroupedSampler(
                self.args.eval_batch_size,
                dataset=eval_dataset,
                lengths=lengths,
                model_input_name=model_input_name,
            )

        if self.args.world_size <= 1:
            return SequentialSampler(eval_dataset)
        else:
            return None