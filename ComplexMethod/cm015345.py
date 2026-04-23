def generate_models(model_directory_path: Path):
    all_models = get_all_models(model_directory_path)
    for a_module, expect_operator in ALL_MODULES.items():
        # For example: TestVersionedDivTensorExampleV7
        torch_module_name = type(a_module).__name__

        if not isinstance(a_module, torch.nn.Module):
            logger.error(
                "The module %s "
                "is not a torch.nn.module instance. "
                "Please ensure it's a subclass of torch.nn.module in fixtures_src.py"
                "and it's registered as an instance in ALL_MODULES in generated_models.py",
                torch_module_name,
            )

        # The corresponding model name is: test_versioned_div_tensor_example_v4
        model_name = "".join(
            [
                "_" + char.lower() if char.isupper() else char
                for char in torch_module_name
            ]
        ).lstrip("_")

        # Some models may not compile anymore, so skip the ones
        # that already has pt file for them.
        logger.info("Processing %s", torch_module_name)
        if model_exist(model_name, all_models):
            logger.info("Model %s already exists, skipping", model_name)
            continue

        script_module = torch.jit.script(a_module)
        actual_model_version = get_output_model_version(script_module)

        current_operator_version = torch._C._get_max_operator_version()
        if actual_model_version >= current_operator_version + 1:
            logger.error(
                "Actual model version %s "
                "is equal or larger than %s + 1. "
                "Please run the script before the commit to change operator.",
                actual_model_version,
                current_operator_version,
            )
            continue

        actual_operator_list = get_operator_list(script_module)
        if expect_operator not in actual_operator_list:
            logger.error(
                "The model includes operator: %s, "
                "however it doesn't cover the operator %s."
                "Please ensure the output model includes the tested operator.",
                actual_operator_list,
                expect_operator,
            )
            continue

        export_model_path = str(model_directory_path / (str(model_name) + ".ptl"))
        script_module._save_for_lite_interpreter(export_model_path)
        logger.info(
            "Generating model %s and it's save to %s", model_name, export_model_path
        )