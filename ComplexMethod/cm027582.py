def get_integration_frame(exclude_integrations: set | None = None) -> IntegrationFrame:
    """Return the frame, integration and integration path of the current stack frame."""
    found_frame = None
    if not exclude_integrations:
        exclude_integrations = set()

    frame: FrameType | None = get_current_frame()
    while frame is not None:
        filename = frame.f_code.co_filename

        for path in ("custom_components/", "homeassistant/components/"):
            try:
                index = filename.index(path)
                start = index + len(path)
                end = filename.index("/", start)
                integration = filename[start:end]
                if integration not in exclude_integrations:
                    found_frame = frame

                break
            except ValueError:
                continue

        if found_frame is not None:
            break

        frame = frame.f_back

    if found_frame is None:
        raise MissingIntegrationFrame

    found_module: str | None = None
    for module, module_obj in dict(sys.modules).items():
        if not hasattr(module_obj, "__file__"):
            continue
        if module_obj.__file__ == found_frame.f_code.co_filename:
            found_module = module
            break

    return IntegrationFrame(
        custom_integration=path == "custom_components/",
        integration=integration,
        module=found_module,
        relative_filename=found_frame.f_code.co_filename[index:],
        frame=found_frame,
    )