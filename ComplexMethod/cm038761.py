def load_data(self) -> None:
        if self.dataset_path is None:
            raise ValueError("dataset_path must be provided for loading data.")

        if not Path(self.dataset_path).is_dir():
            raise ValueError(
                f"dataset_path {self.dataset_path} is not a directory. "
                f"Please make sure to download the dataset from HuggingFace using "
                f"`curl -LsSf {self.DOWNLOAD_SCRIPT_URL} | python3 -`"
            )

        self.data = []

        # Load the JSONL file
        jsonl_data = pd.read_json(
            path_or_buf=Path(self.dataset_path) / f"{self.dataset_subset}.jsonl",
            lines=True,
        )

        # check if the JSONL file has a 'turns' column
        if "messages" not in jsonl_data.columns:
            raise ValueError(
                "JSONL file must contain a 'messages' column. "
                "Please make sure to download the dataset from HuggingFace using "
                f"`curl -LsSf {self.DOWNLOAD_SCRIPT_URL} | python3 -`"
            )

        for _, row in jsonl_data.iterrows():
            # sample only from a specific category if specified
            if (not self.category) or (self.category == row["category"]):
                prompt = row["messages"][0]["content"]
                self.data.append({"prompt": prompt})

        random.seed(self.random_seed)
        if not getattr(self, "disable_shuffle", False):
            random.shuffle(self.data)