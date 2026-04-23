def deprecate_models(models):
    # Get model info
    skipped_models = []
    models_info = defaultdict(dict)
    for model in models:
        single_model_info = extract_model_info(model)
        if single_model_info is None:
            skipped_models.append(model)
        else:
            models_info[model] = single_model_info

    model_config_classes = []
    for model, model_info in models_info.items():
        if model in CONFIG_MAPPING:
            model_config_classes.append(CONFIG_MAPPING[model].__name__)
        elif model_info["model_doc_name"] in CONFIG_MAPPING:
            model_config_classes.append(CONFIG_MAPPING[model_info["model_doc_name"]].__name__)
        else:
            skipped_models.append(model)
            print(f"Model config class not found for model: {model}")

    # Filter out skipped models
    models = [model for model in models if model not in skipped_models]

    if skipped_models:
        print(f"Skipped models: {skipped_models} as the model doc or model path could not be found.")
    print(f"Models to deprecate: {models}")

    # Remove model config classes from config check
    print("Removing model config classes from config checks")
    remove_model_config_classes_from_config_check(model_config_classes)

    tip_message = build_tip_message(get_last_stable_minor_release())

    for model, model_info in models_info.items():
        print(f"Processing model: {model}")
        # Add the tip message to the model doc page directly underneath the title
        print("Adding tip message to model doc page")
        insert_tip_to_model_doc(model_info["model_doc_path"], tip_message)

        # Remove #Copied from statements from model's files
        print("Removing #Copied from statements from model's files")
        remove_copied_from_statements(model)

        # Move the model file to deprecated: src/transformers/models/model -> src/transformers/models/deprecated/model
        print("Moving model files to deprecated for model")
        move_model_files_to_deprecated(model)

        # Delete the model tests: tests/models/model
        print("Deleting model tests")
        delete_model_tests(model)

    # # We do the following with all models passed at once to avoid having to re-write the file multiple times
    print("Updating __init__.py file to point to the deprecated models")
    update_main_init_file(models)

    # Remove model references from other files
    print("Removing model references from other files")
    remove_model_references_from_file(
        "src/transformers/models/__init__.py", models, lambda line, model: model == line.strip().strip(",")
    )
    remove_model_references_from_file(
        "utils/slow_documentation_tests.txt", models, lambda line, model: "/" + model + "/" in line
    )
    remove_model_references_from_file("utils/not_doctested.txt", models, lambda line, model: "/" + model + "/" in line)

    # Add models to DEPRECATED_MODELS in the configuration_auto.py
    print("Adding models to DEPRECATED_MODELS in configuration_auto.py")
    add_models_to_deprecated_models_in_config_auto(models)