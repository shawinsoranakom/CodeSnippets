def validate_prompt(prompt_template: str, *, silent_errors: bool = False, is_mustache: bool = False) -> list[str]:
    if is_mustache:
        # Validate that template doesn't contain complex mustache syntax
        # This must happen before variable extraction to catch patterns like {{#section}}{{/section}}
        validate_mustache_template(prompt_template)

        # Extract only mustache variables
        try:
            input_variables = mustache_template_vars(prompt_template)
        except Exception as exc:
            # Mustache parser errors are often cryptic (e.g., "unclosed tag at line 1")
            # Provide a more helpful error message
            error_str = str(exc).lower()
            if "unclosed" in error_str or "tag" in error_str:
                msg = "Invalid template syntax. Check that all {{variables}} have matching opening and closing braces."
            else:
                msg = f"Invalid mustache template: {exc}"
            raise ValueError(msg) from exc

        # Also get f-string variables to filter them out
        fstring_vars = extract_input_variables_from_prompt(prompt_template)

        # Only keep variables that are actually in mustache syntax (not in f-string syntax)
        # This handles cases where template has both {var} and {{var}}
        input_variables = [v for v in input_variables if v not in fstring_vars or f"{{{{{v}}}}}" in prompt_template]
    else:
        # Extract f-string variables
        input_variables = extract_input_variables_from_prompt(prompt_template)

        # Also get mustache variables to filter them out
        mustache_vars = mustache_template_vars(prompt_template)

        # Only keep variables that are NOT in mustache syntax
        # This handles cases where template has both {var} and {{var}}
        input_variables = [v for v in input_variables if v not in mustache_vars]

    # Check if there are invalid characters in the input_variables
    input_variables = _check_input_variables(input_variables)
    if any(var in _INVALID_NAMES for var in input_variables):
        msg = f"Invalid input variables. None of the variables can be named {', '.join(input_variables)}. "
        raise ValueError(msg)

    try:
        PromptTemplate(template=prompt_template, input_variables=input_variables)
    except Exception as exc:
        msg = f"Invalid prompt: {exc}"
        logger.exception(msg)
        if not silent_errors:
            raise ValueError(msg) from exc

    return input_variables