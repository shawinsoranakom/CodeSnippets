def validate_model(cls, values) -> "OmniWidgetResponseModel":
        """Validate the Omni widget content."""
        # pylint: disable=import-outside-toplevel
        import json  # noqa
        import re
        import pandas as pd

        content = getattr(values, "content", None)

        if content is None:
            raise ValueError("Content cannot be empty.")

        parse_as = getattr(values, "parse_as", None)

        if parse_as and parse_as not in ("table", "chart", "text"):
            raise ValueError(
                "Invalid parse_as value. Must be one of 'table', 'chart', or 'text'."
            )

        # If parameter was supplied, assume the data is formatted correctly.
        if content and parse_as:
            data_format = {
                "data_type": "object",
                "parse_as": parse_as,
            }
            values.data_format = data_format
            del values.parse_as

            return values

        if content.__class__.__name__ == "Figure":
            values.parse_as = "chart"
            try:
                content = content.to_json()
            except Exception as e:
                raise ValueError("Failed to convert chart to JSON") from e
            values.content = content
        elif isinstance(content, dict) and "layout" in content and "data" in content:
            values.parse_as = "chart"
        elif isinstance(content, list) and all(
            isinstance(item, dict) for item in content
        ):
            values.parse_as = "table"
        elif isinstance(content, pd.DataFrame):
            values.parse_as = "table"
            try:
                content = json.loads(content.to_json(orient="records"))
            except Exception as e:
                raise ValueError("Failed to convert DataFrame to JSON") from e
            values.content = content
        elif isinstance(content, dict) and all(
            isinstance(v, list) for v in content.values()
        ):
            values.parse_as = "table"
            try:
                df = pd.DataFrame(content)
                content = json.loads(df.to_json(orient="records"))
            except Exception as e:
                raise ValueError(
                    "Failed to convert dictionary of lists to list of records"
                ) from e
            values.content = content
        elif isinstance(content, str) and content.strip():  # pylint: disable=R0916
            try:
                content = json.loads(content)
            except json.JSONDecodeError:
                # Remove trailing commas in objects and arrays
                try:
                    cleaned_content = re.sub(r",(\s*[}\]])", r"\1", content)
                    content = json.loads(cleaned_content)
                except json.JSONDecodeError:
                    pass

            values.parse_as = "table" if isinstance(content, (list, dict)) else "text"
            values.content = content
        else:
            values.parse_as = "text"

        data_format = {
            "data_type": "object",
            "parse_as": parse_as if parse_as else values.parse_as,
        }
        values.data_format = data_format

        del values.parse_as

        return values