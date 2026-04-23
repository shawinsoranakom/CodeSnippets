def __post_init__(self, **kwargs):
        # BC for the `torch_dtype` argument instead of the simpler `dtype`
        # Do not warn, as it would otherwise always be triggered since most configs on the hub have `torch_dtype`
        if (torch_dtype := kwargs.pop("torch_dtype", None)) is not None:
            # If both are provided, keep `dtype`
            self.dtype = self.dtype if self.dtype is not None else torch_dtype
        if self.dtype is not None and isinstance(self.dtype, str) and is_torch_available():
            # we will start using self.dtype in v5, but to be consistent with
            # from_pretrained's dtype arg convert it to an actual torch.dtype object
            import torch

            self.dtype = getattr(torch, self.dtype)

        # Keep the default value of `num_labels=2` in case users have saved a classfier with 2 labels
        # Our configs prev wouldn't save `id2label` for 2 labels because it is the default. In all other
        # cases we expect the config dict to have an `id2label` field if it's a clf model, or not otherwise
        if self.id2label is None:
            self.num_labels = kwargs.get("num_labels", 2)
        else:
            if kwargs.get("num_labels") is not None and len(self.id2label) != kwargs.get("num_labels"):
                logger.warning(
                    f"You passed `num_labels={kwargs.get('num_labels')}` which is incompatible to "
                    f"the `id2label` map of length `{len(self.id2label)}`."
                )
            # Keys are always strings in JSON so convert ids to int
            self.id2label = {int(key): value for key, value in self.id2label.items()}

        # BC for rotary embeddings. We will pop out legacy keys from kwargs and rename to new format
        if hasattr(self, "rope_parameters"):
            kwargs = self.convert_rope_params_to_dict(**kwargs)
        elif kwargs.get("rope_scaling") and kwargs.get("rope_theta"):
            logger.warning(
                f"{self.__class__.__name__} got `key=rope_scaling` in kwargs but hasn't set it as attribute. "
                "For RoPE standardization you need to set `self.rope_parameters` in model's config. "
            )
            kwargs = self.convert_rope_params_to_dict(**kwargs)

        # Parameters for sequence generation saved in the config are popped instead of loading them.
        for parameter_name in GenerationConfig._get_default_generation_params().keys():
            kwargs.pop(parameter_name, None)

        # Name or path to the pretrained checkpoint
        self._name_or_path = str(kwargs.pop("name_or_path", ""))
        self._commit_hash = kwargs.pop("_commit_hash", None)

        # Attention/Experts implementation to use, if relevant (it sets it recursively on sub-configs)
        self._output_attentions: bool | None = kwargs.pop("output_attentions", False)
        self._attn_implementation: str | None = kwargs.pop("attn_implementation", None)
        self._experts_implementation: str | None = kwargs.pop("experts_implementation", None)

        # Additional attributes without default values
        for key, value in kwargs.items():
            # Check this to avoid deserializing problematic fields from hub configs - they should use the public field
            if key not in ("_attn_implementation_internal", "_experts_implementation_internal"):
                try:
                    setattr(self, key, value)
                except AttributeError as err:
                    logger.error(f"Can't set {key} with value {value} for {self}")
                    raise err