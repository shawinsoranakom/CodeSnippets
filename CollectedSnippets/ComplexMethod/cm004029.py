def __post_init__(self, **kwargs):
        if self.num_key_value_heads is None:
            self.num_key_value_heads = self.num_attention_heads
        self.head_dim = self.head_dim if self.head_dim is not None else self.hidden_size // self.num_attention_heads

        if self.rope_parameters is None:
            self.rope_parameters = {
                "rope_type": "yarn",
                "factor": 32.0,
                "beta_fast": 32.0,
                "beta_slow": 1.0,
                "truncate": False,
                "original_max_position_embeddings": 4096,
            }

        requested_num_labels = kwargs.pop("num_labels", len(OPENAI_PRIVACY_FILTER_NER_LABELS))
        if self.id2label is None and requested_num_labels == len(OPENAI_PRIVACY_FILTER_NER_LABELS):
            self.id2label = dict(enumerate(OPENAI_PRIVACY_FILTER_NER_LABELS))
        elif self.id2label is None:
            self.num_labels = requested_num_labels
        if self.label2id is None and self.id2label is not None:
            self.label2id = {label: idx for idx, label in self.id2label.items()}

        PreTrainedConfig.__post_init__(self, **kwargs)