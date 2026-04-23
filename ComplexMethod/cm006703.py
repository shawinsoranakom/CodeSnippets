def validate_data(cls, values):
        if not isinstance(values, dict):
            msg = "Data must be a dictionary"
            raise ValueError(msg)  # noqa: TRY004
        if "data" not in values or values["data"] is None:
            values["data"] = {}
        if not isinstance(values["data"], dict):
            msg = (
                f"Invalid data format: expected dictionary but got {type(values).__name__}."
                " This will raise an error in version langflow==1.3.0."
            )
            logger.warning(msg)
        # Any other keyword should be added to the data dictionary
        for key in values:
            if key not in values["data"] and key not in {"text_key", "data", "default_value"}:
                values["data"][key] = values[key]
        return values