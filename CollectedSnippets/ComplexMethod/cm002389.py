def build_tiny_model_summary(results, organization=None, token=None):
    """Build a summary: a dictionary of the form
    {
      model architecture name:
        {
          "tokenizer_classes": [...],
          "processor_classes": [...],
          "model_classes": [...],
        }
      ..
    }
    """
    tiny_model_summary = {}
    for config_name in results:
        try:
            processors = [key for key, value in results[config_name]["processor"].items()]
            # TODO: we update `fill_result_with_error`: at the end, with the cond `if len(result["processor"]) == 0`
            #   But sometimes, in `def build`, we can't reach `result["processor"] = {type(p).__name__: p.__class__.__name__ for p in processors}`
            #   (i.e. some other errors occur, like `Sam2VideoConfig`), and we need convert `results[config_name]["processor"]` to avid failure!
            #   (for sam2_video, the error is `"Failed to get tiny config for Sam2VideoConfig: Tiny config not created for sam2_video - no model tester is found in the testing module.`)
            processors = [p.__name__ if not isinstance(p, str) else p for p in processors]
            results[config_name]["processor"] = {x: x for x in processors}
        except Exception:
            # This happens for `VisionEncoderDecoderConfig` and `SpeechEncoderDecoderConfig`.
            # Not a prority however.
            print(config_name)
            print(results[config_name])
            print("******************************")
        tokenizer_classes = sorted(
            [x for x in processors if x.endswith(("TokenizerFast", "Tokenizer", "TokenizersBackend'"))]
        )
        processor_classes = sorted([x for x in processors if x not in tokenizer_classes])

        if "pytorch" not in results[config_name]:
            continue
        for arch_name in results[config_name]["pytorch"]:
            model_classes = [arch_name]
            base_arch_name = arch_name
            # tiny model is not created for `arch_name`
            if results[config_name]["pytorch"][arch_name]["model"] is None:
                model_classes = []
            if base_arch_name not in tiny_model_summary:
                tiny_model_summary[base_arch_name] = {}
            tiny_model_summary[base_arch_name].update(
                {
                    "tokenizer_classes": tokenizer_classes,
                    "processor_classes": processor_classes,
                }
            )
            tiny_model_summary[base_arch_name]["model_classes"] = sorted(
                tiny_model_summary[base_arch_name].get("model_classes", []) + model_classes
            )
            if organization is not None:
                repo_name = f"tiny-random-{base_arch_name}"
                # composite models' checkpoints have more precise repo. names on the Hub.
                if base_arch_name in COMPOSITE_MODELS:
                    repo_name = f"tiny-random-{COMPOSITE_MODELS[base_arch_name]}"
                repo_id = f"{organization}/{repo_name}"
                try:
                    commit_hash = hf_api.repo_info(repo_id, token=token).sha
                except Exception:
                    # The directory is not created, but processor(s) is/are included in `results`.
                    logger.warning(f"Failed to get information for {repo_id}.\n{traceback.format_exc()}")
                    del tiny_model_summary[base_arch_name]
                    continue
                tiny_model_summary[base_arch_name]["sha"] = commit_hash

    return tiny_model_summary