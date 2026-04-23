def __init__(
        self,
        model: PretrainedConfig | dict | None = None,
        method: str | None = "extract_hidden_states",
        **kwargs,
    ):
        assert method == "extract_hidden_states"

        if isinstance(model, dict):
            model_dict = model
            source_text_config = None
        elif isinstance(model, PretrainedConfig):
            model_dict = model.to_dict()
            text_config = model.get_text_config()
            source_text_config = text_config if text_config is not model else None
        else:
            model_dict = {}
            source_text_config = None

        # Combine: model_dict first, then kwargs override
        combined = {**model_dict, **kwargs}
        # Remove architectures from the base, we'll set it explicitly
        combined = {k: v for k, v in combined.items() if k != "architectures"}

        combined["architectures"] = ["ExtractHiddenStatesModel"]

        # to_dict() and kwargs both flatten text_config to a plain dict;
        # downstream get_hf_text_config() needs it as a PretrainedConfig
        # for attribute access. Re-insert the original object.
        if source_text_config is not None:
            combined["text_config"] = source_text_config

        super().__init__(**combined)