def _get_merged_dataset(
    dataset_names: list[str] | None,
    model_args: "ModelArguments",
    data_args: "DataArguments",
    training_args: "Seq2SeqTrainingArguments",
    stage: Literal["pt", "sft", "rm", "ppo", "kto"],
    return_dict: bool = False,
) -> Union["Dataset", "IterableDataset", dict[str, "Dataset"]] | None:
    r"""Return the merged datasets in the standard format."""
    if dataset_names is None:
        return None

    datasets = {}
    for dataset_name, dataset_attr in zip(dataset_names, get_dataset_list(dataset_names, data_args.dataset_dir)):
        if (stage == "rm" and dataset_attr.ranking is False) or (stage != "rm" and dataset_attr.ranking is True):
            raise ValueError("The dataset is not applicable in the current training stage.")

        datasets[dataset_name] = _load_single_dataset(dataset_attr, model_args, data_args, training_args)

    if return_dict:
        return datasets
    else:
        return merge_dataset(list(datasets.values()), data_args, seed=training_args.seed)