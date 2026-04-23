def build(config_class, models_to_create, output_dir, keep_model=False):
    """Create all models for a certain model type.

    Args:
        config_class (`PreTrainedConfig`):
            A subclass of `PreTrainedConfig` that is used to determine `models_to_create`.
        models_to_create (`dict`):
            A dictionary containing the processor/model classes that we want to create the instances. These models are
            of the same model type which is associated to `config_class`.
        output_dir (`str`):
            The directory to save all the checkpoints. Each model architecture will be saved in a subdirectory under
            it.
    """
    if data["training_ds"] is None or data["testing_ds"] is None:
        ds = load_dataset("Salesforce/wikitext", "wikitext-2-raw-v1")
        data["training_ds"] = ds["train"]
        data["testing_ds"] = ds["test"]

    if config_class.model_type in [
        "encoder-decoder",
        "vision-encoder-decoder",
        "speech-encoder-decoder",
        "vision-text-dual-encoder",
    ]:
        return build_composite_models(config_class, output_dir)

    result = {k: {} for k in models_to_create}

    # These will be removed at the end if they are empty
    result["error"] = None
    result["warnings"] = []

    # Build processors
    processor_classes = models_to_create["processor"]

    # AutoTokenizer can't load from hub repo ...
    if config_class.__name__ in ["FastSpeech2ConformerWithHifiGanConfig"]:
        processor_classes = (FastSpeech2ConformerTokenizer,) + processor_classes

    if len(processor_classes) == 0:
        error = f"No processor class could be found in {config_class.__name__}."
        fill_result_with_error(result, error, None, models_to_create)
        logger.error(result["error"][0])
        processor_names = [p.__name__ if not isinstance(p, str) else p for p in result["processor"]]
        result["processor"] = {p: p for p in processor_names}

        return result

    traces = []
    errors = []
    for processor_class in processor_classes:
        try:
            processor = build_processor(config_class, processor_class, allow_no_checkpoint=True)
            if processor is not None:
                if type(processor) not in result["processor"]:
                    result["processor"][type(processor)] = processor
        except Exception:
            error = f"Failed to build processor for {processor_class.__name__}."
            trace = traceback.format_exc()
            errors.append(error)
            traces.append(trace)
            # fill_result_with_error(result, error, trace, models_to_create)
            logger.error((error, trace))
            # TODO: add trace and error anyway?
            # Let's return all what we could build
            # return result

    # TODO: We might get some errors while still having some processors!
    if len(errors) > 0:
        error = "\n".join(errors)
        trace = "\n".join(traces)
        fill_result_with_error(result, error, trace, models_to_create)

    if len(result["processor"]) == 0:
        if config_class.__name__ not in CONFIGS_WITHOUT_PROCESSOR:
            error = f"No processor could be built for {config_class.__name__}."
            fill_result_with_error(result, error, None, models_to_create)
            logger.error(result["error"][0])
            processor_names = [p.__name__ if not isinstance(p, str) else p for p in result["processor"]]
            result["processor"] = {p: p for p in processor_names}
            return result

    try:
        tiny_config = get_tiny_config(config_class)
    except Exception as e:
        error = f"Failed to get tiny config for {config_class.__name__}: {e}"
        trace = traceback.format_exc()
        fill_result_with_error(result, error, trace, models_to_create)
        logger.error(result["error"][0])
        processor_names = [p.__name__ if not isinstance(p, str) else p for p in result["processor"]]
        result["processor"] = {p: p for p in processor_names}
        return result

    # Convert the processors (reduce vocabulary size, smaller image size, etc.)
    processors = list(result["processor"].values())
    processor_output_folder = os.path.join(output_dir, "processors")
    try:
        processors = convert_processors(processors, tiny_config, processor_output_folder, result)
    except Exception:
        error = "Failed to convert the processors."
        trace = traceback.format_exc()
        result["warnings"].append((error, trace))

    # # TODO: if we don't call `convert_processors`, we will need to save here.
    # #   (some conversion might be very slow)
    # processors = [p for p in processors if p is not None]
    # for p in processors:
    #     p.save_pretrained(processor_output_folder)

    if len(processors) == 0:
        if config_class.__name__ not in CONFIGS_WITHOUT_PROCESSOR:
            error = f"No processor is returned by `convert_processors` for {config_class.__name__}."
            fill_result_with_error(result, error, None, models_to_create)
            logger.error(result["error"][0])
            processor_names = [p.__name__ if not isinstance(p, str) else p for p in result["processor"]]
            result["processor"] = {p: p for p in processor_names}
            return result

    try:
        config_overrides = get_config_overrides(config_class, processors)
    except Exception as e:
        error = f"Failure occurs while calling `get_config_overrides`: {e}"
        trace = traceback.format_exc()
        fill_result_with_error(result, error, trace, models_to_create)
        logger.error(result["error"][0])
        processor_names = [p.__name__ if not isinstance(p, str) else p for p in result["processor"]]
        result["processor"] = {p: p for p in processor_names}
        return result

    # Just for us to see this easily in the report
    if "vocab_size" in config_overrides:
        result["vocab_size"] = config_overrides["vocab_size"]

    # Update attributes that `vocab_size` involves
    for k, v in config_overrides.items():
        if hasattr(tiny_config, k):
            setattr(tiny_config, k, v)
        # So far, we only have to deal with `text_config`, as `config_overrides` contains text-related attributes only.
        # `FuyuConfig` saves data under both FuyuConfig and its `text_config`. This is not good, but let's just update
        # every involved fields to avoid potential failure.
        if (
            hasattr(tiny_config, "text_config")
            and tiny_config.text_config is not None
            and hasattr(tiny_config.text_config, k)
        ):
            setattr(tiny_config.text_config, k, v)
            # If `text_config_dict` exists, we need to update its value here too in order to # make
            # `save_pretrained -> from_pretrained` work.
            if hasattr(tiny_config, "text_config_dict"):
                tiny_config.text_config_dict[k] = v

    if result["warnings"]:
        logger.warning(result["warnings"][0][0])

    # update `result["processor"]`
    result["processor"] = {type(p).__name__: p.__class__.__name__ for p in processors}

    for pytorch_arch in models_to_create["pytorch"]:
        result["pytorch"][pytorch_arch.__name__] = {}
        error = None
        try:
            used_tiny_config = tiny_config

            # TODO: Some model_type will include multiple `pytorch_arch` but they might actually have different `self.config_class`
            #   (e.g. Qwen3_5Config from qwen3_5, and `Qwen3_5ForCausalLM`
            #   Let's first try to get the component maybe
            if pytorch_arch.config_class != config_class:
                used_tiny_config = _get_exact_config(tiny_config, pytorch_arch.config_class)

            # TODO: If we can't get the exact config, let's skip to avoid issue
            # TODO: Maybe add as an error info
            if pytorch_arch.config_class != used_tiny_config.__class__:
                print(
                    f"Skip `{pytorch_arch.__name__}`: its config class is {pytorch_arch.config_class} != {used_tiny_config.__class__} Oh la la!!!"
                )
                del result["pytorch"][pytorch_arch.__name__]
                continue

            model = build_model(pytorch_arch, used_tiny_config, output_dir=output_dir, keep_model=keep_model)
        except Exception as e:
            # TODO: hacky way to make `T5GemmaEncoderModel` work
            if pytorch_arch.__name__ == "T5GemmaEncoderModel":
                _tiny_config = copy.deepcopy(tiny_config)
                _tiny_config.is_encoder_decoder = False
                model = build_model(pytorch_arch, _tiny_config, output_dir=output_dir, keep_model=keep_model)
            else:
                model = None
                error = f"Failed to create the pytorch model for {pytorch_arch}: {e}"
                trace = traceback.format_exc()

        result["pytorch"][pytorch_arch.__name__]["model"] = model.__class__.__name__ if model is not None else None
        result["pytorch"][pytorch_arch.__name__]["checkpoint"] = (
            get_checkpoint_dir(output_dir, pytorch_arch) if model is not None else None
        )
        if error is not None:
            result["pytorch"][pytorch_arch.__name__]["error"] = (error, trace)
            logger.error(f"{pytorch_arch.__name__}: {error}")

    if not result["error"]:
        del result["error"]
    if not result["warnings"]:
        del result["warnings"]

    return result