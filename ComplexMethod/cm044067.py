def check_for_platform_extensions(fastapi_app, widgets_to_exclude) -> list:
    """Check for data-processing Platform extensions and add them to the widget exclude filter."""
    to_check_for = ["econometrics", "quantitative", "technical"]
    openapi_tags = fastapi_app.openapi_tags or []
    tags: list = []
    for tag in openapi_tags:
        if any(mod in tag.get("name", "") for mod in to_check_for):
            tags.append(tag.get("name", ""))

    if tags and (any(f"openbb_{mod}" in sys.modules for mod in to_check_for)):
        api_prefix = SystemService().system_settings.api_settings.prefix
        for tag in tags:
            if f"openbb_{tag}" in sys.modules:
                # If the module is loaded, we can safely add it to the exclude filter.
                widgets_to_exclude.append(f"{api_prefix}/{tag}/*")

    return widgets_to_exclude