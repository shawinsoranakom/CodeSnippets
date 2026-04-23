def find_tested_models(test_file: str) -> set[str]:
    """
    Parse the content of test_file to detect what's in `all_model_classes`. This detects the models that inherit from
    the common test class.

    Args:
        test_file (`str`): The path to the test file to check

    Returns:
        `Set[str]`: The set of models tested in that file.
    """
    # TODO Matt: Some of the regexes here are ugly / hacky, and we can probably parse the content better.
    #            Also we should be clear about exactly what rules we're enforcing and which classes
    #            are actually mandatory.
    with open(os.path.join(PATH_TO_TESTS, test_file), "r", encoding="utf-8", newline="\n") as f:
        content = f.read()

    model_tested = set()

    all_models = re.findall(r"all_model_classes\s+=\s+\(\s*\(([^\)]*)\)", content)
    # Check with one less parenthesis as well
    all_models += re.findall(r"all_model_classes\s+=\s+\(([^\)]*)\)", content)
    if len(all_models) > 0:
        for entry in all_models:
            for line in entry.split(","):
                name = line.strip()
                if len(name) > 0:
                    model_tested.add(name)

    # Models that inherit from `CausalLMModelTester` don't need to set `all_model_classes` -- it is built from other
    # attributes by default.
    if "CausalLMModelTester" in content:
        base_model_class = re.findall(r"base_model_class\s+=.*", content)  # Required attribute
        base_class = base_model_class[0].split("=")[1].strip()
        model_tested.add(base_class)

        model_name = base_class.replace("Model", "")
        # Optional attributes: if not set explicitly, the tester will attempt to infer and use the corresponding class
        for test_class_type in [
            "causal_lm_class",
            "sequence_classification_class",
            "question_answering_class",
            "token_classification_class",
        ]:
            tested_class = re.findall(rf"{test_class_type}\s+=.*", content)
            if tested_class:
                tested_class = tested_class[0].split("=")[1].strip()
            else:
                tested_class = model_name + _COMMON_MODEL_NAMES_MAP[test_class_type]
            model_tested.add(tested_class)
    # Same as above, but for VLMModelTester. We scope the search to the VLMModelTester subclass body, as some
    # files may contain both a CausalLMModelTester and a VLMModelTester (e.g. gemma3).
    vlm_class_match = re.search(r"class \w+\(VLMModelTester\)", content)
    if vlm_class_match is not None:
        vlm_content = content[vlm_class_match.start() :]
        base_model_class = re.findall(r"base_model_class\s+=.*", vlm_content)  # Required attribute
        base_class = base_model_class[0].split("=")[1].strip()
        model_tested.add(base_class)

        model_name = base_class.replace("Model", "")
        # Optional attributes: if not set explicitly, the tester will attempt to infer and use the corresponding class
        for test_class_type in [
            "conditional_generation_class",
            "sequence_classification_class",
        ]:
            tested_class = re.findall(rf"{test_class_type}\s+=.*", vlm_content)
            if tested_class:
                tested_class = tested_class[0].split("=")[1].strip()
            elif test_class_type in _VLM_COMMON_MODEL_NAMES_MAP:
                tested_class = model_name + _VLM_COMMON_MODEL_NAMES_MAP[test_class_type]
            else:
                continue
            model_tested.add(tested_class)

    return model_tested