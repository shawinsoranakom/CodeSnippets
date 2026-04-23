def apply_data_references(to_migrate):
    """Apply references."""
    for strings_file in INTEGRATIONS_DIR.glob("*/strings.json"):
        strings = load_json_from_path(strings_file)
        steps = strings.get("config", {}).get("step")

        if not steps:
            continue

        changed = False

        for step_data in steps.values():
            step_data = step_data.get("data", {})
            for key, value in step_data.items():
                if key in to_migrate and value != to_migrate[key]:
                    if key.split("_")[0].lower() in value.lower():
                        step_data[key] = to_migrate[key]
                        changed = True
                    elif value.startswith("[%key"):
                        pass
                    else:
                        print(
                            f"{strings_file}: Skipped swapping '{key}': '{value}' does not contain '{key}'"
                        )

        if not changed:
            continue

        strings_file.write_text(json.dumps(strings, indent=2))