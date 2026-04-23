def validate_port_code(cls, v):
        """Validate port_code."""
        if isinstance(v, str):
            v = [v] if "," not in v else v.split(",")

        if not isinstance(v, list) or not all(isinstance(item, str) for item in v):
            raise OpenBBError("port_code must be a string or a list of strings.")

        port_id_choices = get_port_id_choices()
        port_id_map = {
            choice["value"].lower(): choice["label"] for choice in port_id_choices
        }

        # Create country name to ISO code mapping
        country_name_to_iso = {}
        for iso_code, country_name in PORT_COUNTRIES.items():
            country_name_to_iso[country_name.lower()] = iso_code
            country_name_to_iso[country_name.lower().replace(" ", "_")] = iso_code

        new_values: list = []
        for item in v:
            if item == "all":
                return "all"

            # Try direct ISO country code lookup first
            if item.upper() in PORT_COUNTRIES.values():
                country_ports = get_port_ids_by_country(item)
                if country_ports:
                    new_values.extend(country_ports.split(","))
                    continue

            item_lower = (
                item.lower().split("(")[0].replace(" ", "_")
                if "(" in item
                else item.lower().replace(" ", "_")
            )
            item_lower = item_lower.replace(" - ", "_").replace("-", "_")

            # Accept keys (port IDs)
            if item in port_id_map:
                new_values.append(item)
            # Accept values (port names)
            elif item in port_id_map.values():
                # Find the corresponding port ID
                for k, v_ in port_id_map.items():
                    if v_ == item:
                        new_values.append(k)
                        break
            # Accept lower_snake_case
            elif item_lower in [
                v_.replace(" - ", "_").replace("-", "_").lower().replace(" ", "_")
                for v_ in port_id_map.values()
            ]:
                # Match by value
                values_snake = [
                    v_.replace(" - ", "_").replace("-", "_").lower().replace(" ", "_")
                    for v_ in port_id_map.values()
                ]
                idx = values_snake.index(item_lower)
                new_item = port_id_map[idx]
                new_values.append(new_item)
            # Accept first part of port name (before dash)
            elif item_lower in [
                v_.split(" - ")[0].lower().replace(" ", "_")
                for v_ in port_id_map.values()
            ]:
                first_parts = [
                    v_.split(" - ")[0].lower().replace(" ", "_")
                    for v_ in port_id_map.values()
                ]
                idx = first_parts.index(item_lower)
                new_values.append(list(port_id_map.keys())[idx])
            else:
                raise ValueError(
                    f"Invalid port_code: {item}. Must be a valid port ID or name.Available options: {port_id_choices}."
                )

        if not new_values:
            raise ValueError("No valid port_code provided.")

        return ",".join(new_values)