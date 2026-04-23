def run_build_config(
    custom_component: CustomComponent,
    user_id: str | UUID | None = None,
) -> tuple[dict, CustomComponent]:
    """Builds the field configuration dictionary for a custom component.

    If the input is an instance of a subclass of Component (excluding Component itself), returns its
    build configuration and the instance. Otherwise, evaluates the component's code to create an instance,
    calls its build_config method, and processes any RangeSpec objects in the configuration. Raises an
    HTTP 400 error if the code is missing or invalid, or if instantiation or configuration building fails.

    Returns:
        A tuple containing the field configuration dictionary and the component instance.
    """
    # Check if the instance's class is a subclass of Component (but not Component itself)
    # If we have a Component that is a subclass of Component, that means
    # we have imported it
    # If not, it means the component was loaded through LANGFLOW_COMPONENTS_PATH
    # and loaded from a file
    if is_a_preimported_component(custom_component):
        return custom_component.build_config(), custom_component

    if custom_component._code is None:
        error = "Code is None"
    elif not isinstance(custom_component._code, str):
        error = "Invalid code type"
    else:
        try:
            custom_class = eval_custom_component_code(custom_component._code)
        except Exception as exc:
            logger.exception("Error while evaluating custom component code")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": ("Invalid type conversion. Please check your code and try again."),
                    "traceback": traceback.format_exc(),
                },
            ) from exc

        try:
            custom_instance = custom_class(_user_id=user_id)
            build_config: dict = custom_instance.build_config()

            for field_name, field in build_config.copy().items():
                # Allow user to build Input as well
                # as a dict with the same keys as Input
                field_dict = get_field_dict(field)
                # Let's check if "rangeSpec" is a RangeSpec object
                if "rangeSpec" in field_dict and isinstance(field_dict["rangeSpec"], RangeSpec):
                    field_dict["rangeSpec"] = field_dict["rangeSpec"].model_dump()
                build_config[field_name] = field_dict

        except Exception as exc:
            logger.exception("Error while building field config")
            if hasattr(exc, "detail") and "traceback" in exc.detail:
                logger.error(exc.detail["traceback"])
            raise
        return build_config, custom_instance

    msg = f"Invalid type conversion: {error}. Please check your code and try again."
    logger.error(msg)
    raise HTTPException(
        status_code=400,
        detail={"error": msg},
    )