def find_frontend_states():
    """Find frontend states.

    Source key -> target key
    Add key to integrations strings.json
    """
    path = FRONTEND_REPO / "src/translations/en.json"
    frontend_states = load_json_from_path(path)["state"]

    # domain => state object
    to_write = {}
    to_migrate = {}

    for domain, states in frontend_states.items():
        if domain in SKIP_DOMAIN:
            continue

        to_key_base = f"component::{domain}::state"
        from_key_base = f"state::{domain}"

        if domain in STATES_WITH_DEV_CLASS:
            domain_to_write = dict(states)

            for device_class, dev_class_states in domain_to_write.items():
                to_device_class = "_" if device_class == "default" else device_class
                for key in dev_class_states:
                    to_migrate[f"{from_key_base}::{device_class}::{key}"] = (
                        f"{to_key_base}::{to_device_class}::{key}"
                    )

            # Rewrite "default" device class to _
            if "default" in domain_to_write:
                domain_to_write["_"] = domain_to_write.pop("default")

        else:
            if domain == "group":
                for key in GROUP_DELETE:
                    states.pop(key)

            domain_to_write = {"_": states}

            for key in states:
                to_migrate[f"{from_key_base}::{key}"] = f"{to_key_base}::_::{key}"

        # Map out common values with
        for dev_class_states in domain_to_write.values():
            for key, value in dev_class_states.copy().items():
                if value in STATE_REWRITE:
                    dev_class_states[key] = STATE_REWRITE[value]
                    continue

                match = re.match(r"\[\%key:state::(\w+)::(.+)\%\]", value)

                if not match:
                    continue

                dev_class_states[key] = "[%key:component::{}::state::{}%]".format(
                    *match.groups()
                )

        to_write[domain] = domain_to_write

    for domain, state in to_write.items():
        strings = INTEGRATIONS_DIR / domain / "strings.json"
        if strings.is_file():
            content = load_json_from_path(strings)
        else:
            content = {}

        content["state"] = state
        strings.write_text(json.dumps(content, indent=2) + "\n")

    pprint(to_migrate)

    print()
    while input("Type YES to confirm: ") != "YES":
        pass

    migrate_project_keys_translations(FRONTEND_PROJECT_ID, CORE_PROJECT_ID, to_migrate)