def _merge_kwargs(
        self,
        ModelProcessorKwargs: ProcessingKwargs,
        tokenizer_init_kwargs: dict | None = None,
        **kwargs,
    ) -> dict[str, dict]:
        """
        Method to merge dictionaries of kwargs cleanly separated by modality within a Processor instance.
        The order of operations is as follows:
            1) kwargs passed as before have highest priority to preserve BC.
                ```python
                high_priority_kwargs = {"crop_size" = {"height": 222, "width": 222}, "padding" = "max_length"}
                processor(..., **high_priority_kwargs)
                ```
            2) kwargs passed as modality-specific kwargs have second priority. This is the recommended API.
                ```python
                processor(..., text_kwargs={"padding": "max_length"}, images_kwargs={"crop_size": {"height": 222, "width": 222}}})
                ```
            3) kwargs passed during instantiation of a modality processor have fourth priority.
                ```python
                tokenizer = tokenizer_class(..., {"padding": "max_length"})
                image_processor = image_processor_class(...)
                processor(tokenizer, image_processor) # will pass max_length unless overridden by kwargs at call
                ```
            4) defaults kwargs specified at processor level have lowest priority.
                ```python
                class MyProcessingKwargs(ProcessingKwargs, CommonKwargs, TextKwargs, ImagesKwargs, total=False):
                    _defaults = {
                        "text_kwargs": {
                            "padding": "max_length",
                            "max_length": 64,
                        },
                    }
                ```
        Args:
            ModelProcessorKwargs (`ProcessingKwargs`):
                Typed dictionary of kwargs specifically required by the model passed.
            tokenizer_init_kwargs (`Dict`, *optional*):
                Dictionary of kwargs the tokenizer was instantiated with and need to take precedence over defaults.

        Returns:
            output_kwargs (`Dict`):
                Dictionary of per-modality kwargs to be passed to each modality-specific processor.

        """
        # holding a copy to avoid mutating user-provided arguments
        # Use deepcopy to also copy nested dicts (like videos_kwargs) that will be modified via pop()
        kwargs = copy.deepcopy(kwargs)

        # Initialize dictionaries
        output_kwargs = {
            "text_kwargs": {},
            "images_kwargs": {},
            "audio_kwargs": {},
            "videos_kwargs": {},
        }

        default_kwargs = {
            "text_kwargs": {},
            "images_kwargs": {},
            "audio_kwargs": {},
            "videos_kwargs": {},
        }

        map_preprocessor_kwargs = {
            "text_kwargs": "tokenizer",
            "images_kwargs": "image_processor",
            "audio_kwargs": "feature_extractor",
            "videos_kwargs": "video_processor",
        }

        possible_modality_keywords = {"text", "audio", "videos", "images"}
        used_keys = set()

        # get defaults from set model processor kwargs if they exist
        for modality in default_kwargs:
            default_kwargs[modality] = ModelProcessorKwargs._defaults.get(modality, {}).copy()
            # Some preprocessors define a set of accepted "valid_kwargs" (currently only vision).
            # In those cases, we don’t declare a `ModalityKwargs` attribute in the TypedDict.
            # Instead, we dynamically obtain the kwargs from the preprocessor and merge them
            # with the general kwargs set. This ensures consistency between preprocessor and
            # processor classes, and helps prevent accidental mismatches.
            modality_valid_kwargs = set(ModelProcessorKwargs.__annotations__[modality].__annotations__)
            if modality in map_preprocessor_kwargs:
                preprocessor = getattr(self, map_preprocessor_kwargs[modality], None)
                preprocessor_valid_kwargs = (
                    getattr(preprocessor, "valid_kwargs", None) if preprocessor is not None else None
                )
                modality_valid_kwargs.update(
                    set(preprocessor_valid_kwargs.__annotations__ if preprocessor_valid_kwargs is not None else [])
                )
            # update defaults with arguments from tokenizer init
            for modality_key in modality_valid_kwargs:
                # init with tokenizer init kwargs if necessary
                if tokenizer_init_kwargs is not None and modality_key in tokenizer_init_kwargs:
                    value = (
                        getattr(self.tokenizer, modality_key)
                        if hasattr(self.tokenizer, modality_key)
                        else tokenizer_init_kwargs[modality_key]
                    )
                    default_kwargs[modality][modality_key] = value
        # now defaults kwargs are updated with the tokenizers defaults.
        # pass defaults to output dictionary
        output_kwargs.update(default_kwargs)

        # For `common_kwargs` just update all modality-specific kwargs with same key/values
        common_kwargs = ModelProcessorKwargs._defaults.get("common_kwargs", {})
        common_kwargs.update(kwargs.get("common_kwargs", {}))
        if common_kwargs:
            for kwarg in output_kwargs.values():
                kwarg.update(common_kwargs)

        # update modality kwargs with passed kwargs
        non_modality_kwargs = set(kwargs) - set(output_kwargs)
        for modality, output_kwarg in output_kwargs.items():
            modality_valid_kwargs = set(ModelProcessorKwargs.__annotations__[modality].__annotations__)
            if modality in map_preprocessor_kwargs:
                preprocessor = getattr(self, map_preprocessor_kwargs[modality], None)
                preprocessor_valid_kwargs = (
                    getattr(preprocessor, "valid_kwargs", None) if preprocessor is not None else None
                )
                modality_valid_kwargs.update(
                    set(preprocessor_valid_kwargs.__annotations__ if preprocessor_valid_kwargs is not None else [])
                )
            for modality_key in modality_valid_kwargs:
                # check if we received a structured kwarg dict or not to handle it correctly
                if modality in kwargs:
                    kwarg_value = kwargs[modality].pop(modality_key, "__empty__")
                    # check if this key was passed as a flat kwarg.
                    if kwarg_value != "__empty__" and modality_key in non_modality_kwargs:
                        raise ValueError(
                            f"Keyword argument {modality_key} was passed two times:\n"
                            f"in a dictionary for {modality} and as a **kwarg."
                        )
                elif modality_key in kwargs:
                    # we get a modality_key instead of popping it because modality-specific processors
                    # can have overlapping kwargs
                    kwarg_value = kwargs.get(modality_key, "__empty__")
                else:
                    kwarg_value = "__empty__"
                if not isinstance(kwarg_value, str) or kwarg_value != "__empty__":
                    output_kwarg[modality_key] = kwarg_value
                    used_keys.add(modality_key)

        # Determine if kwargs is a flat dictionary or contains nested dictionaries
        if any(key in default_kwargs for key in kwargs):
            # kwargs is dictionary-based, and some keys match modality names
            for modality, subdict in kwargs.items():
                if modality in default_kwargs:
                    for subkey, subvalue in subdict.items():
                        if subkey not in used_keys:
                            output_kwargs[modality][subkey] = subvalue
                            used_keys.add(subkey)
        else:
            # kwargs is a flat dictionary
            for key, kwarg in kwargs.items():
                if key not in used_keys and key not in possible_modality_keywords:
                    logger.warning_once(
                        f"Keyword argument `{key}` is not a valid argument for this processor and will be ignored."
                    )

        for key, typed_dict_obj in ModelProcessorKwargs.__annotations__.items():
            if key in map_preprocessor_kwargs:
                preprocessor = getattr(self, map_preprocessor_kwargs[key], None)
                if preprocessor is None or getattr(preprocessor, "valid_kwargs", None) is None:
                    continue
                preprocessor_typed_dict_obj = getattr(preprocessor, "valid_kwargs")
                typed_dict_obj = TypedDict(
                    "merged_typed_dict",
                    {**preprocessor_typed_dict_obj.__annotations__, **typed_dict_obj.__annotations__},
                    total=False,
                )
            validate_typed_dict(typed_dict_obj, output_kwargs[key])
        return output_kwargs