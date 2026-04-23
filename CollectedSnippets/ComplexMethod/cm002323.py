def remove_model_config_classes_from_config_check(model_config_classes):
    """
    Remove the deprecated model config classes from the check_config_attributes.py file

    Args:
        model_config_classes (List[str]): The model config classes to remove e.g. ["BertConfig", "DistilBertConfig"]
    """
    filename = REPO_PATH / "utils/check_config_attributes.py"
    with open(filename, "r") as f:
        check_config_attributes = f.read()

    # Keep track as we have to delete comment above too
    in_special_cases_to_allow = False
    in_indent = False
    new_file_lines = []

    for line in check_config_attributes.split("\n"):
        indent = get_line_indent(line)
        if (line.strip() == "SPECIAL_CASES_TO_ALLOW = {") or (line.strip() == "SPECIAL_CASES_TO_ALLOW.update("):
            in_special_cases_to_allow = True

        elif in_special_cases_to_allow and indent == 0 and line.strip() in ("}", ")"):
            in_special_cases_to_allow = False

        if in_indent:
            if line.strip().endswith(("]", "],")):
                in_indent = False
            continue

        if in_special_cases_to_allow and any(
            model_config_class in line for model_config_class in model_config_classes
        ):
            # Remove comments above the model config class to remove
            while new_file_lines[-1].strip().startswith("#"):
                new_file_lines.pop()

            if line.strip().endswith("["):
                in_indent = True

            continue

        elif any(model_config_class in line for model_config_class in model_config_classes):
            continue

        new_file_lines.append(line)

    with open(filename, "w") as f:
        f.write("\n".join(new_file_lines))