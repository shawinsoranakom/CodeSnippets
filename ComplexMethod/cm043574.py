def _prompt_context(preset_extension_types: list[str] | None = None) -> dict:
    context = {}

    context["full_name"] = Prompt.ask("  full_name", default="Hello World")
    context["email"] = Prompt.ask("  email", default="hello@world.com")
    context["project_name"] = Prompt.ask(
        "  project_name", default="OpenBB Python Extension Template"
    )
    default_tag = context["project_name"].lower().replace(" ", "-").replace("_", "-")
    context["project_tag"] = Prompt.ask("  project_tag", default=default_tag)
    default_pkg = context["project_name"].lower().replace(" ", "_").replace("-", "_")
    context["package_name"] = Prompt.ask("  package_name", default=default_pkg)

    if preset_extension_types:
        types = preset_extension_types
    else:
        while True:
            raw = Prompt.ask(
                "  extension_types"
                " - router | provider | obbject | on_command_output | charting | all",
                default="router",
            )
            try:
                types = _parse_extension_types(raw)
                break
            except ValueError as e:
                print(f"  Error: {e}")

    context["extension_types"] = ",".join(types)
    is_all = "all" in types

    if is_all or "provider" in types:
        context["provider_name"] = Prompt.ask("  provider_name", default="template")
    else:
        context["provider_name"] = "template"

    if is_all or "router" in types or "charting" in types:
        context["router_name"] = Prompt.ask("  router_name", default="template")
    else:
        context["router_name"] = "template"

    if is_all or "obbject" in types or "on_command_output" in types:
        context["obbject_name"] = Prompt.ask("  obbject_name", default="template")
    else:
        context["obbject_name"] = "template"

    return context