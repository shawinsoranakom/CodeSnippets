def __post_init__(self):
        # check if the configuration is for a sharded vLLM model
        self._is_sharded = (
            isinstance(self.tensorizer_uri, str)
            and re.search(r"%0\dd", self.tensorizer_uri) is not None
        )

        if self.tensorizer_dir and self.lora_dir:
            raise ValueError(
                "Only one of tensorizer_dir or lora_dir may be specified. "
                "Use lora_dir exclusively when serializing LoRA adapters, "
                "and tensorizer_dir or tensorizer_uri otherwise."
            )
        if self.tensorizer_dir and self.tensorizer_uri:
            logger.warning_once(
                "Provided both tensorizer_dir and tensorizer_uri. "
                "Inferring tensorizer_dir from tensorizer_uri as the "
                "latter takes precedence."
            )
            self.tensorizer_dir = os.path.dirname(self.tensorizer_uri)
        if not self.tensorizer_uri:
            if self.lora_dir:
                self.tensorizer_uri = f"{self.lora_dir}/adapter_model.tensors"
            elif self.tensorizer_dir:
                self.tensorizer_uri = f"{self.tensorizer_dir}/model.tensors"
            else:
                raise ValueError(
                    "Unable to resolve tensorizer_uri. "
                    "A valid tensorizer_uri or tensorizer_dir "
                    "must be provided for deserialization, and a "
                    "valid tensorizer_uri, tensorizer_uri, or "
                    "lora_dir for serialization."
                )
        else:
            self.tensorizer_dir = os.path.dirname(self.tensorizer_uri)

        if not self.serialization_kwargs:
            self.serialization_kwargs = {}
        if not self.deserialization_kwargs:
            self.deserialization_kwargs = {}