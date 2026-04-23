def get_tiny_config(config_class, model_class=None, **model_tester_kwargs):
    """Retrieve a tiny configuration from `config_class` using each model's `ModelTester`.

    Args:
        config_class: Subclass of `PreTrainedConfig`.

    Returns:
        An instance of `config_class` with tiny hyperparameters
    """
    model_type = config_class.model_type

    # For model type like `data2vec-vision` and `donut-swin`, we can't get the config/model file name directly via
    # `model_type` as it would be sth. like `configuration_data2vec_vision.py`.
    # A simple way is to use `inspect.getsourcefile(config_class)`.
    config_source_file = inspect.getsourcefile(config_class)
    # The modeling file name without prefix (`modeling_`) and postfix (`.py`)
    modeling_name = config_source_file.split(os.path.sep)[-1].replace("configuration_", "").replace(".py", "")
    # TODO: remark: several configuration classes might be defined in the same modeling directory.
    #   The test directory is still the same, so we are good here.

    try:
        print("Importing", model_type_to_module_name(model_type))
        module_name = model_type_to_module_name(model_type)
        if not modeling_name.startswith(module_name):
            raise ValueError(f"{modeling_name} doesn't start with {module_name}!")
        test_file = os.path.join("tests", "models", module_name, f"test_modeling_{modeling_name}.py")
        models_to_model_testers = get_model_to_tester_mapping(test_file)
        # Find the model tester class
        model_tester_class = None
        tester_classes = []
        if model_class is not None:
            tester_classes = get_tester_classes_for_model(test_file, model_class)
        else:
            for _tester_classes in models_to_model_testers.values():
                tester_classes.extend(_tester_classes)
        if len(tester_classes) > 0:
            # sort with the length of the class names first, then the alphabetical order
            # This is to avoid `T5EncoderOnlyModelTest` is used instead of `T5ModelTest`, which has
            # `is_encoder_decoder=False` and causes some pipeline tests failing (also failures in `Optimum` CI).
            # TODO: More fine grained control of the desired tester class.
            model_tester_class = min(tester_classes, key=lambda x: (len(x.__name__), x.__name__))

            # TODO: SpeechT5ForSpeechToText needs a particular tester to get the working config
            # TODO: this is hacky however, as all model classes share the same config class but having different tester
            # TODO: make this more flexible and roubst
            if config_class.__name__ == "SpeechT5Config":
                for x in tester_classes:
                    if x.__name__ == "SpeechT5ForSpeechToTextTester":
                        model_tester_class = x
                        break

    except ModuleNotFoundError:
        error = f"Tiny config not created for {model_type} - cannot find the testing module from the model name."
        raise ValueError(error)

    if model_tester_class is None:
        error = f"Tiny config not created for {model_type} - no model tester is found in the testing module."
        raise ValueError(error)

    # CLIP-like models have `text_model_tester` and `vision_model_tester`, and we need to pass `vocab_size` to
    # `text_model_tester` via `text_kwargs`. The same trick is also necessary for `Flava`.

    if "vocab_size" in model_tester_kwargs:
        if "text_kwargs" in inspect.signature(model_tester_class.__init__).parameters:
            vocab_size = model_tester_kwargs.pop("vocab_size")
            model_tester_kwargs["text_kwargs"] = {"vocab_size": vocab_size}

    # `parent` is an instance of `unittest.TestCase`, but we don't need it here.
    model_tester, config = _build_model_tester_and_get_config(model_tester_class, model_tester_kwargs, model_type)

    config = _get_exact_config(config, config_class)

    # TODO: For `pe_audio_video`: the tester only gives `PeAudioVideoEncoderConfig` and can't create model for `PeAudioVideoModel`
    # TODO: This part is necessary for Gemma3Model!
    # TODO: Make this part much better without duplicating the code and less error prone
    if not isinstance(config, config_class):
        model_tester_class_name = config_class_to_model_tester_map.get(config_class.__name__, None)
        if model_tester_class_name is not None:
            test_module = get_test_module(test_file)
            new_model_tester_class = getattr(test_module, model_tester_class_name)

            model_tester, config = _build_model_tester_and_get_config(
                new_model_tester_class, model_tester_kwargs, model_type
            )

        # TODO: Disabled as this causes issues due to much larger models
        # # TODO: For `pe_audio_video`: the tester only gives `PeAudioVideoEncoderConfig` and can't create model for `PeAudioVideoModel`
        # #   we try to find if `config` is a subconfig for `config_class`. If so, return `config_class()` after setting that attr. to `config`
        # # TODO: But this might get very large model?
        # # TODO: This part is necessary for Gemma3Model!
        # config_from_class = config_class()
        # keys = config_from_class.to_dict().keys()
        # for key in keys:
        #     if key.endswith("_config"):
        #         o = getattr(config_from_class, key)
        #         if isinstance(config, o.__class__):
        #             setattr(config_from_class, key, config)
        #             config = config_from_class
        #             break

    # make sure this is long enough (some model tester has `20` for this attr.) to pass `text-generation`
    # pipeline tests.
    max_positions = []
    for key in ["max_position_embeddings", "max_source_positions", "max_target_positions"]:
        if getattr(config, key, 0) > 0:
            max_positions.append(getattr(config, key))
        if getattr(config, "text_config", None) is not None:
            if getattr(config.text_config, key, None) is not None:
                max_positions.append(getattr(config.text_config, key))
    if len(max_positions) > 0:
        max_position = max(200, min(max_positions))
        for key in ["max_position_embeddings", "max_source_positions", "max_target_positions"]:
            if getattr(config, key, 0) > 0:
                setattr(config, key, max_position)
            if getattr(config, "text_config", None) is not None:
                if getattr(config.text_config, key, None) is not None:
                    setattr(config.text_config, key, max_position)

    # TODO: We have this `self.qformer_config.encoder_hidden_size = self.vision_config.hidden_size` in `InstructBlipConfig`,
    #   and we need to do it here otherwise shape issue!!!
    # TODO: But the actual problem is that we should try to get `InstructBlipConfig` in the first place instead of `InstructBlipVisionConfig`.
    # (At this moment, we get tiny `InstructBlipVisionConfig`, and then full `InstructBlipConfig` with tiny `InstructBlipVisionConfig`: from the trick above)
    if config.__class__.__name__ in ["InstructBlipConfig", "InstructBlipVideoConfig"]:
        config.qformer_config.encoder_hidden_size = config.vision_config.hidden_size

    return config