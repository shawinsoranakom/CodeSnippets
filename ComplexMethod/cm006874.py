def update_template_field(new_template, key, previous_value_dict) -> None:
    """Updates a specific field in the frontend template."""
    template_field = new_template.get(key)
    if not template_field or template_field.get("type") != previous_value_dict.get("type"):
        return

    if "value" in previous_value_dict and previous_value_dict["value"] is not None:
        # if the new value is different, this means the default value has been changed
        # so we need to update the value in the template_field
        # and set other parameters to the new ones as well
        if template_field.get("value") != previous_value_dict["value"]:
            template_field["load_from_db"] = previous_value_dict.get("load_from_db", False)
        template_field["value"] = previous_value_dict["value"]

    if previous_value_dict.get("file_path"):
        file_path_value = get_file_path_value(previous_value_dict["file_path"])
        if not file_path_value:
            # If the file does not exist, remove the value from the template_field["value"]
            template_field["value"] = ""
        template_field["file_path"] = file_path_value