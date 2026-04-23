def create_tiny_models(
    output_path,
    all,
    model_types,
    models_to_skip,
    no_check,
    upload,
    organization,
    token,
    num_workers=1,
):
    clone_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    if os.getcwd() != clone_path:
        raise ValueError(f"This script should be run from the root of the clone of `transformers` {clone_path}")

    report_path = os.path.join(output_path, "reports")
    os.makedirs(report_path, exist_ok=True)

    _pytorch_arch_mappings = [x for x in dir(transformers_module) if x.startswith("MODEL_") and x.endswith("_MAPPING")]

    pytorch_arch_mappings = [getattr(transformers_module, x) for x in _pytorch_arch_mappings]

    config_classes = CONFIG_MAPPING.values()
    if not all:
        config_classes = [CONFIG_MAPPING[model_type] for model_type in model_types]

    # TODO: we should add information to the reports instead of skip them
    config_classes = [x for x in config_classes if x.__name__ not in no_model_tester_at_all]
    config_classes = [x for x in config_classes if x.__name__ not in configs_requiring_too_exotic_dependency]
    config_classes = [x for x in config_classes if x.__name__ not in deprecated_models]
    config_classes = [x for x in config_classes if x.__name__ not in config_without_meaningful_model_class]

    # A map from config classes to tuples of processors (tokenizer, feature extractor, processor) classes
    processor_type_map = {c: get_processor_types_from_config_class(c) for c in config_classes}

    to_create = {}
    for c in config_classes:
        processors = processor_type_map[c]
        models = get_architectures_from_config_class(c, pytorch_arch_mappings, models_to_skip)
        if len(models) > 0:
            to_create[c] = {"processor": processors, "pytorch": models}

    results = {}
    if num_workers <= 1:
        for c, models_to_create in list(to_create.items()):
            print(f"Create models for {c.__name__} ...")
            result = build(c, models_to_create, output_dir=os.path.join(output_path, c.model_type))
            results[c.__name__] = result
            print("=" * 40)
    else:
        all_build_args = []
        for c, models_to_create in list(to_create.items()):
            all_build_args.append((c, models_to_create, os.path.join(output_path, c.model_type)))
        with multiprocessing.Pool(processes=num_workers) as pool:
            results = pool.starmap(build, all_build_args)
            results = {build_args[0].__name__: result for build_args, result in zip(all_build_args, results)}

    print(results)

    if upload:
        if organization is None:
            raise ValueError("The argument `organization` could not be `None`. No model is uploaded")

        to_upload = []
        for model_type in os.listdir(output_path):
            # This is the directory containing the reports
            if model_type == "reports":
                continue
            for arch in os.listdir(os.path.join(output_path, model_type)):
                if arch == "processors":
                    continue
                to_upload.append(os.path.join(output_path, model_type, arch))
        to_upload = sorted(to_upload)

        upload_results = {}
        if len(to_upload) > 0:
            for model_dir in to_upload:
                try:
                    upload_model(model_dir, organization, token)
                except Exception as e:
                    error = f"Failed to upload {model_dir}. {e.__class__.__name__}: {e}"
                    logger.error(error)
                    upload_results[model_dir] = error

        with open(os.path.join(report_path, "failed_uploads.json"), "w") as fp:
            json.dump(upload_results, fp, indent=4)

    # Build the tiny model summary file. The `tokenizer_classes` and `processor_classes` could be both empty lists.
    # When using the items in this file to update the file `tests/utils/tiny_model_summary.json`, the model
    # architectures with `tokenizer_classes` and `processor_classes` being both empty should **NOT** be added to
    # `tests/utils/tiny_model_summary.json`.

    tiny_model_summary = build_tiny_model_summary(results, organization=organization, token=token)
    with open(os.path.join(report_path, "tiny_model_summary.json"), "w") as fp:
        json.dump(tiny_model_summary, fp, indent=4)

    with open(os.path.join(report_path, "tiny_model_creation_report.json"), "w") as fp:
        json.dump(results, fp, indent=4)

    # Build the warning/failure report (json format): same format as the complete `results` except this contains only
    # warnings or errors.
    failed_results = build_failed_report(results)
    with open(os.path.join(report_path, "failed_report.json"), "w") as fp:
        json.dump(failed_results, fp, indent=4)

    simple_report, failed_report = build_simple_report(results)
    # The simplified report: a .txt file with each line of format:
    # {model architecture name}: {OK or error message}
    with open(os.path.join(report_path, "simple_report.txt"), "w") as fp:
        fp.write(simple_report)

    # The simplified failure report: same above except this only contains line with errors
    with open(os.path.join(report_path, "simple_failed_report.txt"), "w") as fp:
        fp.write(failed_report)

    update_tiny_model_summary_file(report_path=os.path.join(output_path, "reports"))