def from_trainer(
        cls,
        trainer,
        language=None,
        license=None,
        tags=None,
        model_name=None,
        finetuned_from=None,
        tasks=None,
        dataset_tags=None,
        dataset_metadata=None,
        dataset=None,
        dataset_args=None,
    ):
        # Infer default from dataset
        one_dataset = trainer.eval_dataset if trainer.eval_dataset is not None else trainer.train_dataset
        if is_hf_dataset(one_dataset) and (dataset_tags is None or dataset_args is None or dataset_metadata is None):
            default_tag = one_dataset.builder_name
            # Those are not real datasets from the Hub so we exclude them.
            if default_tag not in ["csv", "json", "pandas", "parquet", "text"]:
                if dataset_metadata is None:
                    dataset_metadata = [{"config": one_dataset.config_name, "split": str(one_dataset.split)}]
                if dataset_tags is None:
                    dataset_tags = [default_tag]
                if dataset_args is None:
                    dataset_args = [one_dataset.config_name]

        if dataset is None and dataset_tags is not None:
            dataset = dataset_tags

        # Infer default finetuned_from
        if (
            finetuned_from is None
            and hasattr(trainer.model.config, "_name_or_path")
            and not os.path.isdir(trainer.model.config._name_or_path)
        ):
            finetuned_from = trainer.model.config._name_or_path

        # Infer default task tag:
        if tasks is None:
            model_class_name = trainer.model.__class__.__name__
            for task, mapping in TASK_MAPPING.items():
                if model_class_name in _get_mapping_values(mapping):
                    tasks = task

        if model_name is None:
            model_name = Path(trainer.args.output_dir).name
        if len(model_name) == 0:
            model_name = finetuned_from

        # Add `generated_from_trainer` to the tags
        if tags is None:
            tags = ["generated_from_trainer"]
        elif isinstance(tags, str) and tags != "generated_from_trainer":
            tags = [tags, "generated_from_trainer"]
        elif "generated_from_trainer" not in tags:
            tags.append("generated_from_trainer")

        _, eval_lines, eval_results = parse_log_history(trainer.state.log_history)
        hyperparameters = extract_hyperparameters_from_trainer(trainer)

        return cls(
            language=language,
            license=license,
            tags=tags,
            model_name=model_name,
            finetuned_from=finetuned_from,
            tasks=tasks,
            dataset=dataset,
            dataset_tags=dataset_tags,
            dataset_args=dataset_args,
            dataset_metadata=dataset_metadata,
            eval_results=eval_results,
            eval_lines=eval_lines,
            hyperparameters=hyperparameters,
        )