def get_tiny_model_summary_from_hub(output_path):
    api = HfApi()
    special_models = COMPOSITE_MODELS.values()

    # All tiny model base names on Hub
    model_names = get_all_model_names()
    models = api.list_models(author="hf-internal-testing")
    _models = set()
    for x in models:
        model = x.id
        org, model = model.split("/")
        if not model.startswith("tiny-random-"):
            continue
        model = model.replace("tiny-random-", "")
        if not model[0].isupper():
            continue
        if model not in model_names and model not in special_models:
            continue
        _models.add(model)

    models = sorted(_models)
    # All tiny model names on Hub
    summary = {}
    for model in models:
        repo_id = f"hf-internal-testing/tiny-random-{model}"
        model = model.split("-")[0]
        try:
            repo_info = api.repo_info(repo_id)
            content = {
                "tokenizer_classes": set(),
                "processor_classes": set(),
                "model_classes": set(),
                "sha": repo_info.sha,
            }
        except Exception:
            continue
        try:
            time.sleep(1)
            tokenizer_fast = AutoTokenizer.from_pretrained(repo_id)
            content["tokenizer_classes"].add(tokenizer_fast.__class__.__name__)
        except Exception as e:
            logger.debug(f"Could not load fast tokenizer for {repo_id}: {e}")
        try:
            time.sleep(1)
            tokenizer_slow = AutoTokenizer.from_pretrained(repo_id, use_fast=False)
            content["tokenizer_classes"].add(tokenizer_slow.__class__.__name__)
        except Exception as e:
            logger.debug(f"Could not load slow tokenizer for {repo_id}: {e}")
        try:
            time.sleep(1)
            img_p = AutoImageProcessor.from_pretrained(repo_id)
            content["processor_classes"].add(img_p.__class__.__name__)
        except Exception as e:
            logger.debug(f"Could not load image processor for {repo_id}: {e}")
        try:
            time.sleep(1)
            feat_p = AutoFeatureExtractor.from_pretrained(repo_id)
            if not isinstance(feat_p, BaseImageProcessor):
                content["processor_classes"].add(feat_p.__class__.__name__)
        except Exception as e:
            logger.debug(f"Could not load feature extractor for {repo_id}: {e}")
        try:
            time.sleep(1)
            model_class = getattr(transformers, model)
            m = model_class.from_pretrained(repo_id)
            content["model_classes"].add(m.__class__.__name__)
        except Exception as e:
            logger.debug(f"Could not load model for {repo_id}: {e}")

        content["tokenizer_classes"] = sorted(content["tokenizer_classes"])
        content["processor_classes"] = sorted(content["processor_classes"])
        content["model_classes"] = sorted(content["model_classes"])

        summary[model] = content
        with open(os.path.join(output_path, "hub_tiny_model_summary.json"), "w") as fp:
            json.dump(summary, fp, ensure_ascii=False, indent=4)