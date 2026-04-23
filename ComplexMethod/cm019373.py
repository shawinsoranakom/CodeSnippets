def tag_modifier(payload):
        """This function will be called by common.py during ANY homestatus call."""
        nonlocal doortag_connectivity, doortag_opening, doortag_timestamp

        if doortag_timestamp is not None:
            payload["time_server"] = doortag_timestamp
        body = payload.get("body", {})

        # Handle both structures: {"home": {...}} AND {"homes": [{...}]}
        homes_to_check = []
        if "home" in body and isinstance(body["home"], dict):
            homes_to_check.append(body["home"])
        elif "homes" in body and isinstance(body["homes"], list):
            homes_to_check.extend(body["homes"])

        for home_data in homes_to_check:
            # Safety check: ensure home_data is actually a dictionary
            if not isinstance(home_data, dict):
                continue

            modules = home_data.get("modules", [])
            for module in modules:
                if isinstance(module, dict) and module.get("id") == doortag_entity_id:
                    module["reachable"] = doortag_connectivity
                    module["status"] = doortag_opening
                    if doortag_timestamp is not None:
                        module["last_seen"] = doortag_timestamp
                    break