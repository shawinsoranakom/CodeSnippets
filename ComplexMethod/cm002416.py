def __init__(
        self,
        batch_size: int,
        dataset: Dataset | None = None,
        lengths: list[int] | None = None,
        model_input_name: str | None = None,
        generator=None,
    ):
        if dataset is None and lengths is None:
            raise ValueError("One of dataset and lengths must be provided.")

        self.batch_size = batch_size
        if lengths is None:
            model_input_name = model_input_name if model_input_name is not None else "input_ids"
            if not isinstance(dataset[0], (dict, BatchEncoding)) or model_input_name not in dataset[0]:
                raise ValueError(
                    "Can only automatically infer lengths for datasets whose items are dictionaries with an "
                    f"'{model_input_name}' key."
                )
            lengths = [len(feature[model_input_name]) for feature in dataset]
        elif isinstance(lengths, torch.Tensor):
            logger.info(
                "If lengths is a torch.Tensor, LengthGroupedSampler will be slow. Converting lengths to list[int]..."
            )
            lengths = lengths.tolist()

        self.lengths = lengths
        self.generator = generator