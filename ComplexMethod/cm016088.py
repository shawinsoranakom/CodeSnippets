def refresh_model_names_and_batch_sizes():
    """
    This function reads the HF Fx tracer supported models and finds the largest
    batch size that could fit on the GPU with PyTorch eager.

    The resulting data is written in huggingface_models_list.txt.

    Note - We only need to run this function if we believe that HF Fx tracer now
    supports more models.
    """
    import transformers.utils.fx as hf_fx

    family = {}
    lm_seen = set()
    family_seen = set()
    for cls_name in hf_fx._SUPPORTED_MODELS:
        if "For" not in cls_name:
            continue

        model_cls = get_module_cls_by_model_name(cls_name)

        # TODO: AttributeError: '*Config' object has no attribute 'vocab_size'
        if model_cls in [
            CLIPModel,
            CLIPVisionModel,
            # SwinForImageClassification,
            # SwinForImageClassification,
            # SwinForMaskedImageModeling,
            # SwinModel,
            ViTForImageClassification,
            ViTForMaskedImageModeling,
            ViTModel,
        ]:
            continue

        # TODO: AssertionError: Padding_idx must be within num_embeddings
        if model_cls in [MarianForCausalLM, MarianMTModel, MarianModel]:
            continue

        # TODO: "model is not supported yet" from HFTracer
        if model_cls in [HubertForSequenceClassification]:
            continue

        # TODO: shape mismatch in loss calculation
        if model_cls in [LxmertForQuestionAnswering]:
            continue

        family_name = cls_name.split("For")[0]
        if family_name not in family:
            family[family_name] = []
        if cls_name.endswith(("MaskedLM", "CausalLM")) and family_name not in lm_seen:
            family[family_name].append(cls_name)
            lm_seen.add(family_name)
        elif (
            cls_name.endswith(
                ("SequenceClassification", "ConditionalGeneration", "QuestionAnswering")
            )
            and family_name not in family_seen
        ):
            family[family_name].append(cls_name)
            family_seen.add(family_name)
        elif cls_name.endswith("ImageClassification"):
            family[family_name].append(cls_name)

    chosen_models = set()
    for members in family.values():
        chosen_models.update(set(members))

    # Add the EXTRA_MODELS
    chosen_models.update(set(EXTRA_MODELS.keys()))

    for model_name in sorted(chosen_models):
        try:
            subprocess.check_call(
                [sys.executable]
                + sys.argv
                + ["--find-batch-sizes"]
                + [f"--only={model_name}"]
                + [f"--output={MODELS_FILENAME}"]
            )
        except subprocess.SubprocessError:
            log.warning(f"Failed to find suitable batch size for {model_name}")